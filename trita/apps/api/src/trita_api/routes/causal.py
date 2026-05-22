"""Causal association + DoWhy pipeline API (F-CAUSAL-001..003)."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, HTTPException, status

from trita_api.auth import TenantDep
from trita_api.db import database_url

router = APIRouter(prefix="/v1/causal", tags=["causal"])


def _causal_unavailable(exc: ImportError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="trita-causal package not installed",
    )


@router.post("/run")
def causal_run(ctx: TenantDep) -> dict[str, object]:
    """Run P-CAUSAL-ASSOC + P-CAUSAL-DOWHY for tenant (JWT tenant_id only)."""
    try:
        from trita_causal.runner import run_causal_pipeline
    except ImportError as exc:
        raise _causal_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            return run_causal_pipeline(conn, ctx.tenant_id)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {exc}",
        ) from exc
