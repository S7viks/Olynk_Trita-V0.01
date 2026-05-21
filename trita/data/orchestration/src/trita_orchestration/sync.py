"""Shopify ingest step — API or in-process (no untrusted tenant_id)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import jwt

from trita_orchestration.env import ensure_api_import_paths, load_repo_env


def _sync_via_api(tenant_id: UUID) -> dict[str, Any]:
    load_repo_env()
    api_base = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET or API_JWT_SECRET required for API ingest mode")
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "tenant_id": str(tenant_id),
        "role": "owner",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=2),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    response = httpx.post(
        f"{api_base}/v1/sources/shopify/sync",
        headers={"Authorization": f"Bearer {token}"},
        timeout=120.0,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Shopify sync API failed: {response.status_code} {response.text[:500]}")
    body = response.json()
    return {
        "mode": "api",
        "events": int(body.get("events", 0)),
        "inserted": int(body.get("inserted", 0)),
        "skipped": int(body.get("skipped", 0)),
        "raw": body,
    }


def _sync_direct(tenant_id: UUID) -> dict[str, Any]:
    ensure_api_import_paths()
    load_repo_env()
    from trita_api.db import get_shopify_credential
    from trita_api.ingest_shopify import sync_records_to_raw
    from trita_api.shopify_oauth import (
        fetch_inventory_levels,
        fetch_orders,
        fetch_products,
    )

    cred = get_shopify_credential(tenant_id)
    if not cred:
        raise RuntimeError("Shopify not connected for pilot tenant — run OAuth first")

    orders = fetch_orders(shop_domain=cred.shop_domain, access_token=cred.access_token)
    inventory = fetch_inventory_levels(
        shop_domain=cred.shop_domain, access_token=cred.access_token
    )
    products = fetch_products(shop_domain=cred.shop_domain, access_token=cred.access_token)
    stats = sync_records_to_raw(
        tenant_id=tenant_id,
        shop_domain=cred.shop_domain,
        orders=orders,
        inventory_levels=inventory,
        products=products,
    )
    if stats["events"] == 0:
        raise RuntimeError("No Shopify records fetched — check scopes and store data")
    return {
        "mode": "direct",
        "orders_fetched": len(orders),
        "inventory_fetched": len(inventory),
        "products_fetched": len(products),
        **stats,
    }


def run_shopify_sync(tenant_id: UUID | None = None) -> dict[str, Any]:
    """Ingest Shopify → raw; tenant from YOGA_BAR_TENANT_ID only."""
    from trita_orchestration.env import pilot_tenant_id

    tid = tenant_id or pilot_tenant_id()
    mode = os.environ.get("TRITA_ORCH_INGEST_MODE", "direct").strip().lower()
    if mode == "api":
        return _sync_via_api(tid)
    return _sync_direct(tid)
