"""Inventory chat API (F-CHAT-001)."""

from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from trita_api.auth import TenantDep, reject_tenant_override
from trita_api.chat.handler import handle_chat_message
from trita_api.db import database_url

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    tenant_id: str | None = None


@router.post("/message")
def chat_message(body: ChatRequest, ctx: TenantDep) -> dict[str, object]:
    override = UUID(body.tenant_id) if body.tenant_id else None
    reject_tenant_override(override, ctx)

    try:
        from trita_decisions.integrity import check_integrity_suppress
    except ImportError:
        check_integrity_suppress = None  # type: ignore[assignment,misc]

    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                suppressed, source = (False, None)
                if check_integrity_suppress:
                    suppressed, source = check_integrity_suppress(cur, ctx.tenant_id)
                return handle_chat_message(
                    cur,
                    tenant_id=ctx.tenant_id,
                    message=body.message,
                    integrity_suppressed=suppressed,
                    integrity_source=source,
                    use_llm=False,
                )
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
