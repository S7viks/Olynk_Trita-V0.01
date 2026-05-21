"""RM-0 gate evidence: Yoga Bar raw + gold + health; no decision tables."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

import psycopg

REPO = Path(__file__).resolve().parents[1]
ENV = REPO / ".env"
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.strip().startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    tid_raw = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not tid_raw or not url:
        print("FAIL: set YOGA_BAR_TENANT_ID and DATABASE_URL in .env")
        return 1

    tenant_id = UUID(tid_raw)
    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from raw.shopify_events where tenant_id = %s",
                (str(tenant_id),),
            )
            raw_n = int(cur.fetchone()[0])
            cur.execute(
                "select count(*) from gold.dim_sku where tenant_id = %s",
                (str(tenant_id),),
            )
            gold_n = int(cur.fetchone()[0])
            cur.execute(
                """
                select status::text, last_sync_at is not null, detail
                from public.integration_health
                where tenant_id = %s and source = 'shopify'
                """,
                (str(tenant_id),),
            )
            health = cur.fetchone()
            cur.execute(
                """
                select table_name from information_schema.tables
                where table_schema = 'public' and table_name ilike '%decision%'
                """
            )
            decision_tables = [r[0] for r in cur.fetchall()]

    print(f"tenant_id={tenant_id}")
    print(f"raw.shopify_events={raw_n}")
    print(f"gold.dim_sku={gold_n}")
    print(f"integration_health={health}")
    print(f"public decision tables={decision_tables}")

    ok = raw_n > 0 and gold_n > 0 and health and health[0] == "healthy" and health[1]
    va12 = len(decision_tables) == 0
    print(f"shopify_to_gold={'PASS' if ok else 'FAIL'}")
    print(f"va12_no_decisions={'PASS' if va12 else 'FAIL'}")
    return 0 if (ok and va12) else 1


if __name__ == "__main__":
    sys.exit(main())
