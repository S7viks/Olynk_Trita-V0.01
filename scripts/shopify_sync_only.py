#!/usr/bin/env python3
"""Step 5 only — POST /v1/sources/shopify/sync (after OAuth callback)."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import jwt

REPO = Path(__file__).resolve().parents[1]
API_BASE = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000").rstrip("/")


def load_env() -> None:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


def mint_jwt(tenant_id: UUID) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "tenant_id": str(tenant_id),
        "role": "owner",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=2),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def main() -> int:
    load_env()
    tenant_id = os.environ.get("YOGA_BAR_TENANT_ID")
    if not tenant_id:
        print("Set YOGA_BAR_TENANT_ID in .env")
        return 1
    token = mint_jwt(UUID(tenant_id))
    r = httpx.post(
        f"{API_BASE}/v1/sources/shopify/sync",
        headers={"Authorization": f"Bearer {token}"},
        timeout=120.0,
    )
    print(f"status: {r.status_code}")
    print(r.text)
    return 0 if r.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
