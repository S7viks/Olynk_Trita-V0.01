"""Inspect / apply migrations on DATABASE_URL from repo .env."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
MIGRATIONS = REPO / "infra" / "supabase" / "migrations"


def load_database_url() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    env_path = REPO / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            return line.split("=", 1)[1]
    raise RuntimeError("DATABASE_URL not found in .env")


def direct_url_from_pooler(pooler_url: str) -> str:
    """Build db.<ref>.supabase.co URL from pooler URL + canonical ref."""
    if "@" not in pooler_url:
        return pooler_url
    prefix, rest = pooler_url.split("@", 1)
    creds = prefix.rsplit("://", 1)[-1]
    if ":" in creds:
        user, password = creds.split(":", 1)
        user = "postgres"
    else:
        password = creds
    return f"postgresql://postgres:{password}@db.{CANONICAL_REF}.supabase.co:5432/postgres"


CANONICAL_REF = "vodcfevbhltftbpjybrf"


def main() -> None:
    pooler = load_database_url()
    url = direct_url_from_pooler(pooler) if "pooler.supabase.com" in pooler else pooler
    print("connecting:", url.split("@")[-1])
    with psycopg.connect(url, connect_timeout=20) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE (table_schema, table_name) IN (
                  ('public','tenants'),
                  ('public','memberships'),
                  ('public','tenant_memberships'),
                  ('raw','shopify_events')
                )
                ORDER BY 1, 2
                """
            )
            print("tables:", cur.fetchall())
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tenants'
                ORDER BY ordinal_position
                """
            )
            print("tenants_columns:", cur.fetchall())


if __name__ == "__main__":
    main()
