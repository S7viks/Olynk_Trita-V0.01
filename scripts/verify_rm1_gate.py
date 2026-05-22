"""RM-1 gate evidence for Yoga Bar: VA-13, VA-14, VA-26."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _pg_connect import connect as pg_connect


def load_env() -> tuple[UUID, str]:
    tenant_raw = None
    url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        print("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required in .env", file=sys.stderr)
        raise SystemExit(1)
    return UUID(tenant_raw), url


def check_va13(cur, tenant_id: UUID) -> tuple[bool, str]:
    cur.execute(
        """
        SELECT
            count(*) AS total,
            count(*) FILTER (WHERE a.canonical_sku_id IS NOT NULL) AS resolved
        FROM gold.fact_order_line AS l
        LEFT JOIN public.sku_alias AS a
            ON l.tenant_id = a.tenant_id
            AND a.source = 'shopify'
            AND a.external_id = l.variant_id
        WHERE l.tenant_id = %s
        """,
        (tenant_id,),
    )
    total, resolved = cur.fetchone()
    total = int(total)
    resolved = int(resolved)
    if total == 0:
        return False, "no order lines — run scripts/seed_yoga_bar_shopify_orders.py + dbt + refresh_identity.py"
    rate = resolved / total
    ok = rate >= 0.9
    return ok, f"lines={total} resolved={resolved} rate={rate:.4f}"


def check_va14(cur, tenant_id: UUID) -> tuple[bool, str]:
    cur.execute(
        "SELECT count(*) FROM gold.dim_sku WHERE tenant_id = %s",
        (tenant_id,),
    )
    dim_count = int(cur.fetchone()[0])
    cur.execute(
        """
        SELECT
            count(*) AS sku_count,
            count(*) FILTER (WHERE stockout_risk) AS stockout,
            count(*) FILTER (WHERE dead_stock) AS dead,
            count(*) FILTER (WHERE cogs_missing) AS cogs_missing,
            coalesce(sum(capital_at_risk), 0) AS capital
        FROM feat.sku_metrics_daily
        WHERE tenant_id = %s
          AND metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
        """,
        (tenant_id, tenant_id),
    )
    row = cur.fetchone()
    if not row or row[0] is None:
        return False, "no feat.sku_metrics_daily rows"
    sku_count = int(row[0])
    aligned = sku_count == dim_count and dim_count > 0
    return (
        aligned,
        f"dim_sku={dim_count} metrics_sku={sku_count} stockout={row[1]} "
        f"dead={row[2]} cogs_missing={row[3]} capital={row[4]}",
    )


def check_va26(cur, tenant_id: UUID) -> tuple[bool, str]:
    cur.execute(
        """
        SELECT count(*)
        FROM public.csv_upload
        WHERE tenant_id = %s AND status = 'completed'::public.csv_upload_status
        """,
        (tenant_id,),
    )
    uploads = int(cur.fetchone()[0])
    cur.execute(
        "SELECT count(*) FROM raw.csv_hub_events WHERE tenant_id = %s",
        (tenant_id,),
    )
    raw_rows = int(cur.fetchone()[0])
    cur.execute(
        """
        SELECT status::text, detail
        FROM public.integration_health
        WHERE tenant_id = %s AND source = 'tally'
        """,
        (tenant_id,),
    )
    tally = cur.fetchone()
    ok = uploads >= 1 and raw_rows >= 1
    if tally:
        detail = tally[1] or {}
        valid = detail.get("valid_count")
        tally_detail = f"tally_status={tally[0]} valid_count={valid}"
    else:
        tally_detail = "tally_health=missing"
    return ok, f"csv_uploads={uploads} raw_rows={raw_rows} {tally_detail}"


def main() -> int:
    tenant_id, url = load_env()
    results: list[tuple[str, bool, str]] = []

    with pg_connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            va13_ok, va13_msg = check_va13(cur, tenant_id)
            va14_ok, va14_msg = check_va14(cur, tenant_id)
            va26_ok, va26_msg = check_va26(cur, tenant_id)

    results = [
        ("VA-13", va13_ok, va13_msg),
        ("VA-14", va14_ok, va14_msg),
        ("VA-26", va26_ok, va26_msg),
    ]

    print(f"tenant_id={tenant_id}")
    all_ok = True
    for name, ok, msg in results:
        print(f"{name}={'PASS' if ok else 'FAIL'}: {msg}")
        all_ok = all_ok and ok

    print(f"rm1_gate={'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
