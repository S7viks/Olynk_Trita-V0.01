"""Find working Supabase pooler for a project ref."""
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

pwd = "Olynktrita234321"
refs = ["bmfakoiiebmsgdtimwdu", "ftidfmfrsplgpcuvzdqv", "uieltrycgbeyebvaalqm"]
hosts = [
    "aws-0-ap-south-1.pooler.supabase.com",
    "aws-1-ap-south-1.pooler.supabase.com",
    "aws-0-us-east-1.pooler.supabase.com",
    "aws-1-ap-southeast-1.pooler.supabase.com",
]
for ref in refs:
    for host in hosts:
        for port in (6543, 5432):
            url = f"postgresql://postgres.{ref}:{pwd}@{host}:{port}/postgres"
            try:
                with psycopg.connect(url, connect_timeout=8) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select 1")
                    print("OK", ref, host, port)
            except Exception:
                pass
