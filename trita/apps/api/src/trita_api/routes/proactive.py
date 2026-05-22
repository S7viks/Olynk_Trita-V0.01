"""Proactive feed and digest API (F-PROACTIVE-*)."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, HTTPException, status

from trita_api.auth import TenantDep
from trita_api.db import database_url

router = APIRouter(prefix="/v1/proactive", tags=["proactive"])


def _unavailable(exc: ImportError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="trita-proactive package not installed",
    )


@router.get("/feed")
def proactive_feed(ctx: TenantDep, limit: int = 50) -> dict[str, object]:
    try:
        from trita_proactive.feed import list_feed
    except ImportError as exc:
        raise _unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                items = list_feed(cur, ctx.tenant_id, limit=min(limit, 100))
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"tenant_id": str(ctx.tenant_id), "count": len(items), "items": items}


@router.post("/run-triggers")
def proactive_run_triggers(ctx: TenantDep) -> dict[str, object]:
    try:
        from trita_proactive.runner import run_proactive_triggers
        from trita_decisions.integrity import check_integrity_suppress
    except ImportError as exc:
        raise _unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                suppressed, source = check_integrity_suppress(cur, ctx.tenant_id)
            result = run_proactive_triggers(
                conn,
                ctx.tenant_id,
                integrity_suppressed=suppressed,
                integrity_source=source,
            )
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return result


@router.post("/digest/weekly")
def proactive_weekly_digest(ctx: TenantDep) -> dict[str, object]:
    try:
        from trita_proactive.digest import send_weekly_digest
    except ImportError as exc:
        raise _unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                return send_weekly_digest(cur, ctx.tenant_id)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
