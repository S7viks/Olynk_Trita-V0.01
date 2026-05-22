"""CSV hub API (F-CONN-005)."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from trita_api.auth import TenantDep, reject_tenant_override
from trita_api.csv_hub.ingest import process_csv_upload
from trita_api.csv_hub.db import get_csv_upload, reset_csv_hub_source
from trita_api.csv_hub.templates import list_templates
from trita_api.integration_health import upsert_integration_health

router = APIRouter(prefix="/v1/csv", tags=["csv"])

CSV_RESET_SOURCES = frozenset({"tally", "delhivery", "generic"})


@router.get("/templates")
def csv_templates() -> dict[str, object]:
    return {"templates": list_templates()}


@router.get("/uploads/{upload_id}")
def csv_upload_status(upload_id: UUID, ctx: TenantDep) -> dict[str, object]:
    row = get_csv_upload(ctx.tenant_id, upload_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return {"tenant_id": str(ctx.tenant_id), **row}


@router.post("/upload")
async def csv_upload(
    ctx: TenantDep,
    file: UploadFile = File(...),
    logical_source: str | None = Form(default=None),
    entity_type: str | None = Form(default=None),
    template_id: str | None = Form(default=None),
    column_map: str | None = Form(default=None),
    tenant_id: str | None = Form(default=None),
) -> dict[str, object]:
    if tenant_id:
        try:
            reject_tenant_override(UUID(tenant_id), ctx)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    parsed_map: dict[str, str] | None = None
    if column_map:
        try:
            parsed_map = json.loads(column_map)
            if not isinstance(parsed_map, dict):
                raise ValueError("column_map must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid column_map: {exc}",
            ) from exc

    try:
        result = process_csv_upload(
            tenant_id=ctx.tenant_id,
            file_name=file.filename or "upload.csv",
            content=content,
            logical_source=logical_source,
            entity_type=entity_type,
            template_id=template_id,
            column_map=parsed_map,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CSV ingest failed: {exc}",
        ) from exc

    return {
        "tenant_id": str(ctx.tenant_id),
        "upload_id": str(result.upload_id),
        "logical_source": result.logical_source,
        "entity_type": result.entity_type,
        "template_id": result.template_id,
        "status": result.status,
        "row_count": result.row_count,
        "valid_count": result.valid_count,
        "quarantine_count": result.quarantine_count,
        "inserted": result.inserted,
        "skipped": result.skipped,
        "idempotent_replay": result.idempotent_replay,
    }


@router.post("/reset")
def csv_reset(
    ctx: TenantDep,
    source: str = Query(..., description="Logical source: tally, delhivery, or generic"),
) -> dict[str, object]:
    """Delete CSV hub uploads/raw/quarantine for a source (disconnect + clear for re-upload)."""
    logical = source.strip().lower()
    if logical not in CSV_RESET_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"source must be one of: {', '.join(sorted(CSV_RESET_SOURCES))}",
        )
    try:
        counts = reset_csv_hub_source(tenant_id=ctx.tenant_id, logical_source=logical)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CSV reset failed: {exc}",
        ) from exc

    health_source = "tally" if logical == "tally" else logical
    upsert_integration_health(
        tenant_id=ctx.tenant_id,
        source=health_source,
        status="disconnected",
        detail={
            "connected": False,
            "message": "CSV data cleared — upload again to reconnect",
            "mode": "csv_hub",
        },
        freshness_sla_hours=168 if health_source == "tally" else 24,
    )
    return {"tenant_id": str(ctx.tenant_id), "source": logical, **counts}
