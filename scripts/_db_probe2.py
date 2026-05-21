"""Probe MCP Supabase project pooler connectivity."""
from __future__ import annotations

import os
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, value = line.partition("=")
    os.environ.setdefault(key.strip(), value.strip())

pwd = os.environ.get("SUPABASE_DB_PASSWORD", "Olynktrita234321")
ref = "bmfakoiiebmsgdtimwdu"
urls = [
    f"postgresql://postgres.{ref}:{pwd}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    f"postgresql://postgres.{ref}:{pwd}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
]
for url in urls:
    print(url.split("@")[1])
    try:
        with psycopg.connect(url, connect_timeout=15) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='tenants'"
                )
                print("  cols", [r[0] for r in cur.fetchall()])
    except Exception as exc:
        print("  FAIL", exc)
