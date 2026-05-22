"""Per-connector connect + sync (F-CONN-002, 004, 006)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from trita_api.auth import TenantDep, reject_tenant_override
from trita_api.connectors.ingest import sync_source
from trita_api.connectors.registry import RM1_API_SOURCES, get_spec
from trita_api.crypto import encrypt_token
from trita_api.db import get_connector_credential, upsert_connector_credential
from trita_api.integration_health import upsert_integration_health

router = APIRouter(prefix="/v1/sources", tags=["sources"])


class ConnectBody(BaseModel):
    """API key connect — never send tenant_id in body."""

    tenant_id: UUID | None = None
    account_ref: str | None = Field(default=None, description="Facility / merchant ref")
    api_key: str | None = None
    api_secret: str | None = None
    email: str | None = None
    password: str | None = None
    key_id: str | None = None
    key_secret: str | None = None
    base_url: str | None = None
    access_token: str | None = None


def _validate_source(source: str) -> str:
    key = source.strip().lower()
    if key not in RM1_API_SOURCES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown connector")
    return key


def _secret_payload(body: ConnectBody, source: str) -> dict[str, str]:
    data: dict[str, str] = {}
    if body.api_key:
        data["api_key"] = body.api_key
    if body.api_secret:
        data["api_secret"] = body.api_secret
    if body.key_id:
        data["key_id"] = body.key_id
    if body.key_secret:
        data["key_secret"] = body.key_secret
    if body.email:
        data["email"] = body.email
    if body.password:
        data["password"] = body.password
    if body.base_url:
        data["base_url"] = body.base_url
    if body.access_token:
        data["access_token"] = body.access_token
    if not data and os.environ.get("CONNECTOR_DEV_FIXTURES", "").lower() in ("1", "true", "yes"):
        data["mode"] = "fixture"
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide API credentials or enable CONNECTOR_DEV_FIXTURES",
        )
    return data


@router.post("/{source}/connect")
def connect_source(source: str, body: ConnectBody, ctx: TenantDep) -> dict[str, object]:
    reject_tenant_override(body.tenant_id, ctx)
    key = _validate_source(source)
    spec = get_spec(key)
    secret = _secret_payload(body, key)
    account_ref = body.account_ref or os.environ.get(f"{key.upper()}_ACCOUNT_REF", "default")
    upsert_connector_credential(
        tenant_id=ctx.tenant_id,
        source=key,
        account_ref=account_ref,
        access_token_encrypted=encrypt_token(json.dumps(secret)),
        scopes="api",
    )
    upsert_integration_health(
        tenant_id=ctx.tenant_id,
        source=key,
        status="degraded",
        detail={
            "connected": True,
            "account_ref": account_ref,
            "message": "Connected — run sync for first ingest",
            "mode": secret.get("mode", "api"),
        },
        freshness_sla_hours=spec.freshness_sla_hours,
    )
    return {"source": key, "connected": True, "account_ref": account_ref}


@router.post("/{source}/sync")
def sync_connector_route(source: str, ctx: TenantDep) -> dict[str, object]:
    key = _validate_source(source)
    spec = get_spec(key)
    cred = get_connector_credential(ctx.tenant_id, key)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{spec.display_name} not connected for this tenant",
        )
    try:
        stats = sync_source(tenant_id=ctx.tenant_id, source=key, cred=cred)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{spec.display_name} sync failed: {exc}",
        ) from exc
    if stats["events"] == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No records fetched",
        )
    now = datetime.now(UTC)
    upsert_integration_health(
        tenant_id=ctx.tenant_id,
        source=key,
        status="healthy",
        last_sync_at=now,
        detail={
            "connected": True,
            "account_ref": stats.get("account_ref"),
            "events": stats["events"],
            "inserted": stats.get("inserted"),
            "ingest_mode": stats.get("ingest_mode"),
        },
        freshness_sla_hours=spec.freshness_sla_hours,
    )
    return {"tenant_id": str(ctx.tenant_id), **stats}
