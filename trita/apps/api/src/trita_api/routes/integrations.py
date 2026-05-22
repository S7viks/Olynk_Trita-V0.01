"""Integration health API (F-CONN-HEALTH, VA-06)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from trita_api.auth import TenantDep
from trita_api.connectors.registry import CONNECTOR_SOURCES
from trita_api.db import get_connector_credential, get_shopify_credential
from trita_api.integration_health import IntegrationHealthRow, list_integration_health

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

# Sources UI: production RM-1 + beta RM-3 (honest disconnected until connect/sync)
SOURCES_UI_ORDER = (
    "shopify",
    "unicommerce",
    "tally",
    "shiprocket",
    "razorpay",
    "delhivery",
    "meta_ads",
    "google_ads",
)


def _row_to_dict(row: IntegrationHealthRow) -> dict[str, object]:
    last_sync: str | None = None
    if row.last_sync_at is not None:
        last_sync = row.last_sync_at.astimezone().isoformat()
    spec = CONNECTOR_SOURCES.get(row.source)
    return {
        "source": row.source,
        "display_name": spec.display_name if spec else row.source,
        "mode": spec.mode if spec else "api",
        "tier": spec.tier if spec else "production",
        "status": row.status,
        "last_sync_at": last_sync,
        "freshness_sla_hours": row.freshness_sla_hours,
        "detail": row.detail,
        "updated_at": row.updated_at.astimezone().isoformat(),
    }


def _default_row(
    source: str,
    *,
    connected: bool,
    status: str,
    message: str | None = None,
    account_ref: str | None = None,
) -> IntegrationHealthRow:
    spec = CONNECTOR_SOURCES[source]
    detail: dict[str, object] = {"connected": connected}
    if message:
        detail["message"] = message
    if account_ref:
        detail["account_ref"] = account_ref
    if spec.mode == "csv_hub":
        detail["requires"] = "F-CONN-005"
    return IntegrationHealthRow(
        source=source,
        status=status,
        last_sync_at=None,
        freshness_sla_hours=spec.freshness_sla_hours,
        detail=detail,
        updated_at=datetime.now().astimezone(),
    )


def _resolve_row(
    source: str,
    stored: dict[str, IntegrationHealthRow],
    ctx_tenant_id,
) -> IntegrationHealthRow:
    spec = CONNECTOR_SOURCES[source]
    if source in stored:
        row = stored[source]
        detail = dict(row.detail or {})
        if spec.mode == "csv_hub" or detail.get("mode") == "csv_hub" or detail.get("upload_id"):
            has_upload = bool(detail.get("upload_id") or detail.get("valid_count"))
            detail["connected"] = has_upload
            if not detail.get("message"):
                detail["message"] = (
                    "Upload via CSV hub"
                    if has_upload
                    else "Upload a Tally CSV via CSV hub (F-CONN-005)"
                )
            return IntegrationHealthRow(
                source=row.source,
                status=row.status,
                last_sync_at=row.last_sync_at,
                freshness_sla_hours=row.freshness_sla_hours,
                detail=detail,
                updated_at=row.updated_at,
            )
        if source == "shopify":
            cred = get_shopify_credential(ctx_tenant_id)
            detail["connected"] = cred is not None
            if cred:
                detail.setdefault("shop_domain", cred.shop_domain)
            return IntegrationHealthRow(
                source=row.source,
                status=row.status,
                last_sync_at=row.last_sync_at,
                freshness_sla_hours=row.freshness_sla_hours,
                detail=detail or None,
                updated_at=row.updated_at,
            )
        cred = get_connector_credential(ctx_tenant_id, source)
        detail["connected"] = cred is not None
        if cred:
            detail.setdefault("account_ref", cred.account_ref)
        return IntegrationHealthRow(
            source=row.source,
            status=row.status,
            last_sync_at=row.last_sync_at,
            freshness_sla_hours=row.freshness_sla_hours,
            detail=detail or None,
            updated_at=row.updated_at,
        )

    if spec.mode == "csv_hub":
        return _default_row(
            source,
            connected=False,
            status="disconnected",
            message="Connect via CSV hub (F-CONN-005) — not API sync",
        )

    cred = get_connector_credential(ctx_tenant_id, source)
    if source == "shopify":
        cred_shop = get_shopify_credential(ctx_tenant_id)
        if cred_shop:
            return _default_row(
                source,
                connected=True,
                status="degraded",
                message="Connected — run sync for first ingest",
                account_ref=cred_shop.shop_domain,
            )
        return _default_row(source, connected=False, status="disconnected")

    if cred:
        return _default_row(
            source,
            connected=True,
            status="degraded",
            message="Connected — run sync for first ingest",
            account_ref=cred.account_ref,
        )
    return _default_row(source, connected=False, status="disconnected")


@router.get("/health")
def integrations_health(ctx: TenantDep) -> dict[str, object]:
    """Tenant-scoped connector health for Sources UI."""
    stored = {r.source: r for r in list_integration_health(ctx.tenant_id)}
    integrations = [
        _row_to_dict(_resolve_row(source, stored, ctx.tenant_id))
        for source in SOURCES_UI_ORDER
    ]
    return {"tenant_id": str(ctx.tenant_id), "integrations": integrations}
