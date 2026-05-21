"""One-off DB probe for steps 4-5 (not committed long-term)."""
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

url = os.environ["DATABASE_URL"]
print("connecting...", url.split("@")[-1])
with psycopg.connect(url, connect_timeout=20) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'tenants'
            ORDER BY ordinal_position
            """
        )
        cols = [r[0] for r in cur.fetchall()]
        print("columns:", cols)
        cur.execute("SELECT id, slug FROM public.tenants WHERE slug = %s", ("yoga-bar",))
        print("yoga-bar:", cur.fetchone())
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'raw' AND table_name = 'shopify_events'"
        )
        print("raw.shopify_events exists:", cur.fetchone()[0] == 1)
