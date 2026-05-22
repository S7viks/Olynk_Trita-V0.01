"""VA-14 / F-METRICS gate: feat.sku_metrics_daily aligns with gold.dim_sku."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _pg_connect import connect as pg_connect


def load_env() -> tuple[str, str]:
    tenant = None
    db_url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            db_url = line.split("=", 1)[1].strip()
    if not tenant or not db_url:
        raise RuntimeError("YOGA_BAR_TENANT_ID and DATABASE_URL required in .env")
    return tenant, db_url


def main() -> int:
    tenant_id, url = load_env()
    with pg_connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM gold.dim_sku WHERE tenant_id = %s::uuid",
                (tenant_id,),
            )
            dim_count = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT count(*) FROM feat.sku_metrics_daily
                WHERE tenant_id = %s::uuid
                  AND metric_date = (
                      SELECT max(metric_date) FROM feat.sku_metrics_daily
                      WHERE tenant_id = %s::uuid
                  )
                """,
                (tenant_id, tenant_id),
            )
            metrics_count = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT
                    count(*) FILTER (WHERE stockout_risk) AS stockout,
                    count(*) FILTER (WHERE dead_stock) AS dead,
                    count(*) FILTER (WHERE cogs_missing) AS no_cogs,
                    coalesce(sum(capital_at_risk), 0) AS capital
                FROM feat.sku_metrics_daily
                WHERE tenant_id = %s::uuid
                  AND metric_date = (
                      SELECT max(metric_date) FROM feat.sku_metrics_daily
                      WHERE tenant_id = %s::uuid
                  )
                """,
                (tenant_id, tenant_id),
            )
            flags = cur.fetchone()

    print(f"tenant_id={tenant_id}")
    print(f"gold.dim_sku={dim_count}")
    print(f"feat.sku_metrics_daily={metrics_count}")
    print(
        f"stockout_risk={flags[0]} dead_stock={flags[1]} "
        f"cogs_missing={flags[2]} capital_at_risk_total={flags[3]}"
    )

    if dim_count == 0:
        print("FAIL: no dim_sku rows", file=sys.stderr)
        return 1
    if metrics_count != dim_count:
        print("FAIL: metrics row count != dim_sku", file=sys.stderr)
        return 1
    print("PASS: metrics mart aligned with dim_sku")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
