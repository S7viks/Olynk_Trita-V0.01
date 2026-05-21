"""Shopify OAuth connect + API sync (VA-04 webhooks deferred)."""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse

from trita_api.auth import TenantDep
from trita_api.crypto import encrypt_token
from trita_api.db import get_shopify_credential, upsert_shopify_credential
from trita_api.ingest_shopify import sync_records_to_raw
from trita_api.shopify_oauth import (
    authorize_url,
    build_oauth_state,
    exchange_code,
    fetch_inventory_levels,
    fetch_orders,
    fetch_products,
    normalize_shop_domain,
    scopes,
    verify_oauth_state,
)

router = APIRouter(prefix="/v1/sources/shopify", tags=["shopify"])


def _default_shop() -> str:
    return os.environ.get("YOGA_BAR_SHOP_DOMAIN", "tritabyolynk.myshopify.com").strip()


@router.get("/connect")
def shopify_connect(
    ctx: TenantDep,
    shop: str = Query(default="", description="Shop domain, e.g. tritabyolynk or tritabyolynk.myshopify.com"),
) -> RedirectResponse:
    """Start Shopify OAuth — tenant_id from JWT only."""
    shop_domain = normalize_shop_domain(shop or _default_shop())
    state = build_oauth_state(tenant_id=str(ctx.tenant_id), shop_domain=shop_domain)
    url = authorize_url(shop_domain=shop_domain, state=state)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", response_model=None)
def shopify_callback(
    code: str | None = Query(None),
    shop: str | None = Query(None),
    state: str | None = Query(None),
) -> RedirectResponse | HTMLResponse:
    """OAuth callback — exchanges code and stores encrypted token server-side."""
    if not code or not shop or not state:
        tenant_hint = os.environ.get("YOGA_BAR_TENANT_ID", "<tenant-uuid>")
        start = (
            f"http://127.0.0.1:8000/dev/shopify/go"
            f"?tenant_id={tenant_hint}&shop=tritabyolynk"
        )
        return HTMLResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"""<!DOCTYPE html><html><body>
<h1>Shopify OAuth not started</h1>
<p>This URL is only used <em>after</em> Shopify redirects back from install/authorize.</p>
<p>Do not open <code>/callback</code> directly.</p>
<p><a href="{start}">Start Shopify connect (step 4)</a></p>
</body></html>""",
        )
    try:
        parsed = verify_oauth_state(state)
        tenant_id = UUID(parsed["tenant_id"])
        shop_domain = normalize_shop_domain(shop)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        ) from exc

    if normalize_shop_domain(shop) != normalize_shop_domain(parsed["shop"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop domain mismatch",
        )

    try:
        token_payload = exchange_code(shop_domain=shop_domain, code=code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shopify token exchange failed",
        ) from exc

    access_token = str(token_payload.get("access_token", ""))
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shopify returned no access_token",
        )

    upsert_shopify_credential(
        tenant_id=tenant_id,
        shop_domain=shop_domain,
        access_token_encrypted=encrypt_token(access_token),
        scopes=scopes(),
    )

    if os.environ.get("ENVIRONMENT", "development") == "development":
        api_base = os.environ.get("NEXT_PUBLIC_API_URL", "http://127.0.0.1:8000").rstrip("/")
        return RedirectResponse(
            url=f"{api_base}/dev/shopify/connected",
            status_code=status.HTTP_302_FOUND,
        )
    web_base = os.environ.get("NEXT_PUBLIC_WEB_URL", "http://localhost:3000").rstrip("/")
    return RedirectResponse(
        url=f"{web_base}/sources?shopify=connected",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/sync")
def shopify_sync(ctx: TenantDep) -> dict[str, object]:
    """Pull orders + inventory via Admin API → raw.shopify_events (idempotent)."""
    cred = get_shopify_credential(ctx.tenant_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify not connected for this tenant",
        )

    warnings: list[str] = []
    try:
        orders = fetch_orders(shop_domain=cred.shop_domain, access_token=cred.access_token)
        if not orders:
            warnings.append(
                "orders empty or blocked (protected customer data approval may be required)"
            )
        inventory = fetch_inventory_levels(
            shop_domain=cred.shop_domain, access_token=cred.access_token
        )
        products = fetch_products(
            shop_domain=cred.shop_domain, access_token=cred.access_token
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shopify API fetch failed",
        ) from exc

    stats = sync_records_to_raw(
        tenant_id=ctx.tenant_id,
        shop_domain=cred.shop_domain,
        orders=orders,
        inventory_levels=inventory,
        products=products,
    )
    if stats["events"] == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No Shopify records fetched — check scopes and store data",
        )
    return {
        "tenant_id": str(ctx.tenant_id),
        "shop_domain": cred.shop_domain,
        "orders_fetched": len(orders),
        "inventory_fetched": len(inventory),
        "products_fetched": len(products),
        "warnings": warnings,
        **stats,
    }


@router.get("/status")
def shopify_status(ctx: TenantDep) -> dict[str, object]:
    """Connection status without returning secrets."""
    cred = get_shopify_credential(ctx.tenant_id)
    if not cred:
        return {"connected": False, "shop_domain": None}
    return {
        "connected": True,
        "shop_domain": cred.shop_domain,
        "scopes": cred.scopes,
    }
