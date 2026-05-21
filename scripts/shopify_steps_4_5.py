#!/usr/bin/env python3
"""
Steps 4 & 5 for Yoga Bar (run on your machine after 1–3).

  Step 4: Open Shopify OAuth (browser)
  Step 5: POST sync → raw.shopify_events

Requires: API running (uvicorn), YOGA_BAR_TENANT_ID in .env
"""

from __future__ import annotations

import os
import sys
import webbrowser
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import jwt

REPO = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def resolve_tenant_id() -> UUID:
    if tid := os.environ.get("YOGA_BAR_TENANT_ID", "").strip():
        return UUID(tid)
    sys.path.insert(0, str(REPO / "scripts"))
    from supabase_rest import get_tenant_by_slug

    row = get_tenant_by_slug("yoga-bar")
    if not row:
        raise SystemExit(
            "No yoga-bar tenant. Add YOGA_BAR_TENANT_ID=<uuid> to .env "
            "(Supabase → tenants where slug = yoga-bar)."
        )
    return UUID(row["id"])


def mint_jwt(tenant_id: UUID) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise SystemExit("SUPABASE_JWT_SECRET required in .env")
    return jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "tenant_id": str(tenant_id),
            "role": "owner",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(hours=2),
        },
        secret,
        algorithm="HS256",
    )


def main() -> int:
    load_env()
    api = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
    tenant_id = resolve_tenant_id()
    os.environ["YOGA_BAR_TENANT_ID"] = str(tenant_id)

    # Health check
    try:
        h = httpx.get(f"{api}/health", timeout=5.0)
        h.raise_for_status()
    except Exception as exc:
        print(f"API not reachable at {api}/health — start server first:")
        print("  cd trita/apps/api")
        print("  pip install -e . ../../data/dlt")
        print("  uvicorn trita_api.main:app --reload --port 8000")
        print(f"  ({exc})")
        return 1

    # Step 4 — browser OAuth (dev route, no Bearer header needed)
    shop = os.environ.get("YOGA_BAR_SHOP_DOMAIN", "tritabyolynk.myshopify.com").split(".")[0]
    connect_url = f"{api}/dev/shopify/go?tenant_id={tenant_id}&shop={shop}"
    print("Step 4 — opening Shopify OAuth in browser:")
    print(connect_url)
    webbrowser.open(connect_url)
    input("After Shopify redirects back (sources?shopify=connected), press Enter for step 5...")

    # Step 5 — sync
    token = mint_jwt(tenant_id)
    r = httpx.post(
        f"{api}/v1/sources/shopify/sync",
        headers={"Authorization": f"Bearer {token}"},
        timeout=120.0,
    )
    print(f"Step 5 — sync status {r.status_code}")
    print(r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)
    return 0 if r.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
