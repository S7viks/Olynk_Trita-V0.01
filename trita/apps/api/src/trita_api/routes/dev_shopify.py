"""Development-only helpers for Shopify OAuth in browser (ENVIRONMENT=development)."""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse

import psycopg

from trita_api.db import database_url
from trita_api.shopify_oauth import authorize_url, build_oauth_state, normalize_shop_domain

router = APIRouter(prefix="/dev/shopify", tags=["dev"])


def _dev_only() -> None:
    if os.environ.get("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="dev only")


@router.get("/connect", response_class=HTMLResponse)
def dev_connect_page(
    tenant_id: UUID = Query(..., description="Yoga Bar tenant UUID from public.tenants"),
    shop: str = Query(default="tritabyolynk"),
) -> str:
    """Step 4 in browser: open /dev/shopify/connect?tenant_id=<uuid>&shop=tritabyolynk"""
    _dev_only()
    shop_domain = normalize_shop_domain(shop)
    state = build_oauth_state(tenant_id=str(tenant_id), shop_domain=shop_domain)
    url = authorize_url(shop_domain=shop_domain, state=state)
    return f"""<!DOCTYPE html>
<html><body>
<p>Trita — Shopify OAuth (dev)</p>
<p>Tenant: {tenant_id}</p>
<p>Shop: {shop_domain}</p>
<p><a href="{url}">Connect Shopify</a></p>
</body></html>"""


@router.post("/seed-yoga-bar")
def seed_yoga_bar() -> dict[str, str]:
    """Ensure Yoga Bar tenant exists; returns tenant_id for steps 4–5."""
    _dev_only()
    with psycopg.connect(database_url(), connect_timeout=30, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tenants'
                  AND column_name IN ('display_name', 'name')
                """
            )
            label_cols = {r[0] for r in cur.fetchall()}
            if "display_name" in label_cols:
                cur.execute(
                    """
                    INSERT INTO public.tenants (slug, display_name)
                    VALUES ('yoga-bar', 'Yoga Bar')
                    ON CONFLICT (slug) DO UPDATE SET display_name = EXCLUDED.display_name
                    RETURNING id
                    """
                )
            elif "name" in label_cols:
                cur.execute(
                    """
                    INSERT INTO public.tenants (slug, name)
                    VALUES ('yoga-bar', 'Yoga Bar')
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="tenants table missing display_name/name column",
                )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="seed failed")
    return {"tenant_id": str(row[0]), "slug": "yoga-bar"}


@router.get("/connected", response_class=HTMLResponse)
def dev_connected() -> str:
    """Shown after successful OAuth in development (replaces localhost:3000/sources)."""
    _dev_only()
    tenant_id = os.environ.get("YOGA_BAR_TENANT_ID", "")
    return f"""<!DOCTYPE html>
<html><body>
<h1>Shopify connected</h1>
<p>Token saved for tenant <code>{tenant_id or "(see .env YOGA_BAR_TENANT_ID)"}</code>.</p>
<p><strong>Step 5:</strong> from repo root run:</p>
<pre>python scripts/shopify_sync_only.py</pre>
<p>Or check status: <a href="/v1/sources/shopify/status">/v1/sources/shopify/status</a> (requires Bearer JWT).</p>
</body></html>"""


@router.get("/go")
def dev_connect_redirect(
    tenant_id: UUID = Query(...),
    shop: str = Query(default="tritabyolynk"),
) -> RedirectResponse:
    _dev_only()
    shop_domain = normalize_shop_domain(shop)
    state = build_oauth_state(tenant_id=str(tenant_id), shop_domain=shop_domain)
    return RedirectResponse(authorize_url(shop_domain=shop_domain, state=state))
