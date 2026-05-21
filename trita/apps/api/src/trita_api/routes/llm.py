"""LLM draft routes — LiteLLM proxy with tenant budget (F-PLAT-003)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from trita_api.auth import TenantDep, reject_tenant_override
from trita_api.llm_budget import tenant_token_budget, tokens_used
from trita_api.llm_client import complete_draft

router = APIRouter(prefix="/v1/llm", tags=["llm"])


class DraftRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    purpose: str = Field(default="card_copy", pattern="^(card_copy|chat)$")
    tenant_id: UUID | None = None


@router.post("/draft")
def llm_draft(body: DraftRequest, ctx: TenantDep) -> dict[str, object]:
    """Narrative draft only; deterministic engine owns inventory numbers (VA-03)."""
    reject_tenant_override(body.tenant_id, ctx)
    result = complete_draft(
        tenant_id=ctx.tenant_id,
        prompt=body.prompt,
        purpose=body.purpose,
    )
    return {
        "tenant_id": str(ctx.tenant_id),
        "purpose": body.purpose,
        "budget_limit": tenant_token_budget(),
        **result,
    }


@router.get("/budget")
def llm_budget(ctx: TenantDep) -> dict[str, object]:
    """Inspect current tenant token usage against cap."""
    return {
        "tenant_id": str(ctx.tenant_id),
        "tokens_used": tokens_used(ctx.tenant_id),
        "budget_limit": tenant_token_budget(),
    }
