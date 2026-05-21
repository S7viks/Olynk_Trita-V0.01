from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from trita_api.auth import TenantDep, TenantContext, reject_tenant_override

router = APIRouter(prefix="/v1/tenant", tags=["tenant"])


class TenantProbeBody(BaseModel):
    tenant_id: UUID | None = None


@router.get("/context")
def tenant_context(ctx: TenantDep) -> dict[str, str]:
    return {
        "user_id": str(ctx.user_id),
        "tenant_id": str(ctx.tenant_id),
        "role": ctx.role,
    }


@router.post("/probe")
def tenant_probe(body: TenantProbeBody, ctx: TenantDep) -> dict[str, str]:
    reject_tenant_override(body.tenant_id, ctx)
    return {"tenant_id": str(ctx.tenant_id), "status": "ok"}
