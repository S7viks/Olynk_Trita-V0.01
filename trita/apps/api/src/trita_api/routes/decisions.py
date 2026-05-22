"""Decision emit, inbox, and audit API (F-DEC-*, F-INBOX-*)."""

from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from trita_api.auth import TenantDep
from trita_api.db import database_url

router = APIRouter(prefix="/v1/decisions", tags=["decisions"])

SYSTEM_EMIT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class RejectBody(BaseModel):
    reason_enum: str = Field(min_length=1)
    reason_text: str | None = None
    tenant_id: UUID | None = None


class SnoozeBody(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    tenant_id: UUID | None = None


def _decisions_unavailable(exc: ImportError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="trita-decisions package not installed",
    )


def _db_error(exc: psycopg.Error) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database error: {exc}",
    )


@router.post("/emit")
def decisions_emit(ctx: TenantDep) -> dict[str, object]:
    """Run deterministic emitter for tenant (P-DECISION-EMIT)."""
    try:
        from trita_decisions.emitter import emit_decisions
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            return emit_decisions(conn, ctx.tenant_id)
    except psycopg.Error as exc:
        raise _db_error(exc) from exc


@router.get("")
def list_decisions(
    ctx: TenantDep,
    tab: str = Query(default="open", pattern="^(open|snoozed|done)$"),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, object]:
    """List inbox cards (F-INBOX-001)."""
    try:
        from trita_decisions.inbox import list_inbox
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    effective_tab = tab
    if status_filter == "snoozed":
        effective_tab = "snoozed"
    elif status_filter in ("approved", "rejected"):
        effective_tab = "done"

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                items = list_inbox(cur, ctx.tenant_id, tab=effective_tab, limit=limit)
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    return {"tenant_id": str(ctx.tenant_id), "tab": effective_tab, "count": len(items), "items": items}


@router.get("/reject-reasons")
def reject_reasons() -> dict[str, object]:
    from trita_decisions.audit import REJECT_REASONS

    return {"reasons": sorted(REJECT_REASONS)}


@router.get("/{decision_id}")
def get_decision_detail(decision_id: UUID, ctx: TenantDep) -> dict[str, object]:
    """Card detail + timeline (F-INBOX-002, F-INBOX-004)."""
    try:
        from trita_decisions.inbox import decision_with_timeline
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                detail = decision_with_timeline(cur, ctx.tenant_id, decision_id)
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return {"tenant_id": str(ctx.tenant_id), "decision": detail}


@router.get("/{decision_id}/timeline")
def get_decision_timeline(decision_id: UUID, ctx: TenantDep) -> dict[str, object]:
    try:
        from trita_decisions.audit import list_audit_timeline
        from trita_decisions.inbox import get_decision
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                if not get_decision(cur, ctx.tenant_id, decision_id):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Decision not found",
                    )
                entries = list_audit_timeline(cur, ctx.tenant_id, decision_id)
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    return {"tenant_id": str(ctx.tenant_id), "decision_id": str(decision_id), "entries": entries}


@router.post("/{decision_id}/approve")
def approve_decision(decision_id: UUID, ctx: TenantDep) -> dict[str, object]:
    try:
        from trita_decisions.inbox import approve_decision as do_approve
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                result = do_approve(
                    cur,
                    tenant_id=ctx.tenant_id,
                    decision_id=decision_id,
                    user_id=ctx.user_id,
                )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    return {"tenant_id": str(ctx.tenant_id), **result}


@router.post("/{decision_id}/reject")
def reject_decision_route(
    decision_id: UUID,
    body: RejectBody,
    ctx: TenantDep,
) -> dict[str, object]:
    if body.tenant_id is not None and body.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="tenant_id mismatch")

    try:
        from trita_decisions.inbox import reject_decision as do_reject
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                result = do_reject(
                    cur,
                    tenant_id=ctx.tenant_id,
                    decision_id=decision_id,
                    user_id=ctx.user_id,
                    reason_enum=body.reason_enum,
                    reason_text=body.reason_text,
                )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    return {"tenant_id": str(ctx.tenant_id), **result}


@router.post("/{decision_id}/snooze")
def snooze_decision_route(
    decision_id: UUID,
    body: SnoozeBody,
    ctx: TenantDep,
) -> dict[str, object]:
    if body.tenant_id is not None and body.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="tenant_id mismatch")

    try:
        from trita_decisions.inbox import snooze_decision as do_snooze
    except ImportError as exc:
        raise _decisions_unavailable(exc) from exc

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                result = do_snooze(
                    cur,
                    tenant_id=ctx.tenant_id,
                    decision_id=decision_id,
                    user_id=ctx.user_id,
                    days=body.days,
                )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise _db_error(exc) from exc

    return {"tenant_id": str(ctx.tenant_id), **result}
