#!/usr/bin/env python3
"""Steps 4–5: Shopify OAuth connect URL + sync (Yoga Bar tenant)."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import jwt
import psycopg

REPO = Path(__file__).resolve().parents[1]
API_BASE = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000").rstrip("/")


def load_env() -> None:
    env_path = REPO / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def database_url() -> str:
    return os.environ["DATABASE_URL"]


def yoga_bar_tenant_id() -> UUID:
    with psycopg.connect(database_url(), connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM public.tenants WHERE slug = %s",
                ("yoga-bar",),
            )
            row = cur.fetchone()
    if not row:
        raise RuntimeError("yoga-bar tenant missing — run seed migration first")
    return row[0]


def mint_jwt(tenant_id: UUID, user_id: UUID | None = None) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET or API_JWT_SECRET required")
    user_id = user_id or UUID("00000000-0000-0000-0000-000000000001")
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": "owner",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=2),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def has_shopify_credentials(tenant_id: UUID) -> bool:
    with psycopg.connect(database_url(), connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM public.connector_credentials
                WHERE tenant_id = %s AND source = 'shopify'
                """,
                (tenant_id,),
            )
            return cur.fetchone() is not None


def main() -> int:
    load_env()
    sys.path.insert(0, str(REPO / "trita" / "data" / "dlt" / "src"))
    sys.path.insert(0, str(REPO / "trita" / "apps" / "api" / "src"))

    tenant_id = yoga_bar_tenant_id()
    token = mint_jwt(tenant_id)
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Yoga Bar tenant_id: {tenant_id}")

    # Step 4 — connect (redirect to Shopify OAuth)
    if not has_shopify_credentials(tenant_id):
        with httpx.Client(follow_redirects=False, timeout=30.0) as client:
            r = client.get(
                f"{API_BASE}/v1/sources/shopify/connect",
                params={"shop": os.environ.get("YOGA_BAR_SHOP_DOMAIN", "tritabyolynk.myshopify.com").replace(".myshopify.com", "")},
                headers=headers,
            )
        if r.status_code != 302:
            print(f"connect failed: {r.status_code} {r.text}")
            return 1
        print("Step 4 — open this URL in a browser (approve app), then re-run this script:")
        print(r.headers.get("location"))
        return 2
    print("Step 4 — already connected (credentials in DB)")

    # Step 5 — sync
    with httpx.Client(timeout=120.0) as client:
        r = client.post(f"{API_BASE}/v1/sources/shopify/sync", headers=headers)
    if r.status_code != 200:
        print(f"sync failed: {r.status_code} {r.text}")
        return 1
    print("Step 5 — sync OK:")
    print(r.json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
