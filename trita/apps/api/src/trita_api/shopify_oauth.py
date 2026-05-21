"""Shopify OAuth + Admin API (no webhooks in this path)."""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

SHOPIFY_SCOPES_DEFAULT = "read_orders,read_inventory,read_products"
API_VERSION = "2024-10"


def _client_id() -> str:
    cid = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
    if not cid:
        raise RuntimeError("SHOPIFY_CLIENT_ID is not configured")
    return cid


def _client_secret() -> str:
    secret = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("SHOPIFY_CLIENT_SECRET is not configured")
    return secret


def _jwt_secret() -> str:
    return (
        os.environ.get("SUPABASE_JWT_SECRET")
        or os.environ.get("API_JWT_SECRET")
        or ""
    )


def redirect_uri() -> str:
    uri = (
        os.environ.get("SHOPIFY_OAUTH_REDIRECT_URI")
        or os.environ.get("SHOPIFY_REDIRECT_URI")
        or ""
    ).strip()
    if not uri:
        api_base = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        uri = f"{api_base}/v1/sources/shopify/callback"
    return uri


def scopes() -> str:
    return os.environ.get("SHOPIFY_SCOPES", SHOPIFY_SCOPES_DEFAULT).strip()


def normalize_shop_domain(shop: str) -> str:
    shop = shop.strip().lower()
    shop = re.sub(r"^https?://", "", shop)
    shop = shop.split("/")[0]
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"
    return shop


def build_oauth_state(*, tenant_id: str, shop_domain: str) -> str:
    payload = {
        "tenant_id": tenant_id,
        "shop": shop_domain,
        "purpose": "shopify_oauth",
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def verify_oauth_state(state: str) -> dict[str, str]:
    payload = jwt.decode(state, _jwt_secret(), algorithms=["HS256"])
    if payload.get("purpose") != "shopify_oauth":
        raise ValueError("invalid oauth state")
    tenant_id = str(payload["tenant_id"])
    shop = str(payload["shop"])
    return {"tenant_id": tenant_id, "shop": shop}


def authorize_url(*, shop_domain: str, state: str) -> str:
    shop = normalize_shop_domain(shop_domain)
    query = urlencode(
        {
            "client_id": _client_id(),
            "scope": scopes(),
            "redirect_uri": redirect_uri(),
            "state": state,
        }
    )
    return f"https://{shop}/admin/oauth/authorize?{query}"


def exchange_code(*, shop_domain: str, code: str) -> dict[str, Any]:
    shop = normalize_shop_domain(shop_domain)
    url = f"https://{shop}/admin/oauth/access_token"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            url,
            json={
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()


def fetch_orders(*, shop_domain: str, access_token: str, limit: int = 50) -> list[dict[str, Any]]:
    """Orders may 403 until app is approved for protected customer data — returns []."""
    shop = normalize_shop_domain(shop_domain)
    url = f"https://{shop}/admin/api/{API_VERSION}/orders.json"
    headers = {"X-Shopify-Access-Token": access_token}
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, headers=headers, params={"status": "any", "limit": limit})
        if response.status_code == 403:
            return []
        response.raise_for_status()
        return response.json().get("orders", [])


def fetch_products(*, shop_domain: str, access_token: str, limit: int = 50) -> list[dict[str, Any]]:
    shop = normalize_shop_domain(shop_domain)
    url = f"https://{shop}/admin/api/{API_VERSION}/products.json"
    headers = {"X-Shopify-Access-Token": access_token}
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, headers=headers, params={"limit": limit})
        response.raise_for_status()
        return response.json().get("products", [])


def fetch_inventory_levels(
    *, shop_domain: str, access_token: str, limit: int = 50
) -> list[dict[str, Any]]:
    shop = normalize_shop_domain(shop_domain)
    headers = {"X-Shopify-Access-Token": access_token}
    with httpx.Client(timeout=60.0) as client:
        loc_resp = client.get(
            f"https://{shop}/admin/api/{API_VERSION}/locations.json",
            headers=headers,
        )
        if loc_resp.status_code >= 400:
            return []
        location_ids = [str(loc["id"]) for loc in loc_resp.json().get("locations", []) if loc.get("id")]
        if not location_ids:
            return []
        inv_resp = client.get(
            f"https://{shop}/admin/api/{API_VERSION}/inventory_levels.json",
            headers=headers,
            params={"location_ids": ",".join(location_ids[:10]), "limit": limit},
        )
        if inv_resp.status_code >= 400:
            return []
        return inv_resp.json().get("inventory_levels", [])
