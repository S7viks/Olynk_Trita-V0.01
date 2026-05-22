"""Apply infra/supabase/migrations to DATABASE_URL in .env (project vodcfevbhltftbpjybrf)."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO / "infra" / "supabase" / "migrations"
CANONICAL_REF = "vodcfevbhltftbpjybrf"

MIGRATION_ORDER = [
    "20260520100000_tenants_memberships.sql",
    "20260520100001_seed_yoga_bar_dev.sql",
    "20260520200000_raw_shopify_events.sql",
    "20260520300000_connector_credentials.sql",
    "20260520400000_graph_schemas.sql",
    "20260520500000_integration_health.sql",
    "20260520600000_connector_raw_rm1.sql",
    "20260520700000_csv_hub.sql",
    "20260520800000_identity_v1.sql",
    "20260520900000_feat_schema.sql",
]


def load_database_url() -> str:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            return line.split("=", 1)[1]
    raise RuntimeError("DATABASE_URL= not set in .env")


def direct_url(pooler_url: str) -> str:
    prefix, _ = pooler_url.split("@", 1)
    password = prefix.rsplit(":", 1)[-1]
    return (
        f"postgresql://postgres:{password}"
        f"@db.{CANONICAL_REF}.supabase.co:5432/postgres"
    )


def main() -> int:
    pooler = load_database_url()
    url = direct_url(pooler) if "pooler.supabase.com" in pooler else pooler
    if CANONICAL_REF not in url and CANONICAL_REF not in pooler:
        print(
            f"WARN: DATABASE_URL does not contain project ref {CANONICAL_REF}",
            file=sys.stderr,
        )
    with psycopg.connect(url, connect_timeout=30) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for name in MIGRATION_ORDER:
                path = MIGRATIONS_DIR / name
                sql = path.read_text(encoding="utf-8")
                print(f"Applying {name} ...")
                try:
                    cur.execute(sql)
                    print(f"  OK")
                except psycopg.errors.DuplicateObject:
                    print(f"  SKIP (already exists)")
                except psycopg.errors.DuplicateTable:
                    print(f"  SKIP (table exists)")
                except psycopg.Error as exc:
                    print(f"  FAIL: {exc}")
                    return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
