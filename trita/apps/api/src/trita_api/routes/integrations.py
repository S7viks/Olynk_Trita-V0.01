"""Integration health API (F-CONN-HEALTH, VA-06)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from trita_api.auth import TenantDep
from trita_api.db import get_shopify_credential
from trita_api.integration_health import IntegrationHealthRow, list_integration_health

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

SHOPIFY_SOURCE = "shopify"


def _row_to_dict(row: IntegrationHealthRow) -> dict[str, object]:
    last_sync: str | None = None
    if row.last_sync_at is not None:
        last_sync = row.last_sync_at.astimezone().isoformat()
    return {
        "source": row.source,
        "status": row.status,
        "last_sync_at": last_sync,
        "freshness_sla_hours": row.freshness_sla_hours,
        "detail": row.detail,
        "updated_at": row.updated_at.astimezone().isoformat(),
    }


@router.get("/health")
def integrations_health(ctx: TenantDep) -> dict[str, object]:
    """Tenant-scoped connector health rows (Phase 0: Shopify only in UI)."""
    rows = {r.source: r for r in list_integration_health(ctx.tenant_id)}
    cred = get_shopify_credential(ctx.tenant_id)

    if SHOPIFY_SOURCE not in rows:
        if cred:
            rows[SHOPIFY_SOURCE] = IntegrationHealthRow(
                source=SHOPIFY_SOURCE,
                status="degraded",
                last_sync_at=None,
                freshness_sla_hours=24,
                detail={
                    "connected": True,
                    "shop_domain": cred.shop_domain,
                    "message": "Connected — run sync for first ingest",
                },
                updated_at=datetime.now().astimezone(),
            )
        else:
            rows[SHOPIFY_SOURCE] = IntegrationHealthRow(
                source=SHOPIFY_SOURCE,
                status="disconnected",
                last_sync_at=None,
                freshness_sla_hours=24,
                detail={"connected": False},
                updated_at=datetime.now().astimezone(),
            )

    shopify = rows[SHOPIFY_SOURCE]
    detail = dict(shopify.detail or {})
    if cred:
        detail["connected"] = True
        detail.setdefault("shop_domain", cred.shop_domain)
    else:
        detail["connected"] = False
    shopify = IntegrationHealthRow(
        source=shopify.source,
        status=shopify.status,
        last_sync_at=shopify.last_sync_at,
        freshness_sla_hours=shopify.freshness_sla_hours,
        detail=detail or None,
        updated_at=shopify.updated_at,
    )

    return {
        "tenant_id": str(ctx.tenant_id),
        "integrations": [_row_to_dict(shopify)],
    }
