"""Onboarding status and completion (F-ONBOARD-001)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from trita_api.auth import TenantDep
from trita_api.db import (
    complete_tenant_onboarding,
    get_onboarding_status,
    update_tenant_display_name,
)

router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


class OnboardingStatusResponse(BaseModel):
    tenant_id: str
    display_name: str
    slug: str
    onboarding_complete: bool
    shopify_connected: bool


class OnboardingProfileBody(BaseModel):
    company_name: str = Field(min_length=1, max_length=120)


@router.get("/status", response_model=OnboardingStatusResponse)
def onboarding_status(ctx: TenantDep) -> OnboardingStatusResponse:
    row = get_onboarding_status(ctx.tenant_id)
    return OnboardingStatusResponse(
        tenant_id=str(row.tenant_id),
        display_name=row.display_name,
        slug=row.slug,
        onboarding_complete=row.onboarding_complete,
        shopify_connected=row.shopify_connected,
    )


@router.patch("/profile", response_model=OnboardingStatusResponse)
def onboarding_update_profile(
    body: OnboardingProfileBody,
    ctx: TenantDep,
) -> OnboardingStatusResponse:
    update_tenant_display_name(ctx.tenant_id, body.company_name)
    row = get_onboarding_status(ctx.tenant_id)
    return OnboardingStatusResponse(
        tenant_id=str(row.tenant_id),
        display_name=row.display_name,
        slug=row.slug,
        onboarding_complete=row.onboarding_complete,
        shopify_connected=row.shopify_connected,
    )


@router.post("/complete", response_model=OnboardingStatusResponse)
def onboarding_complete(ctx: TenantDep) -> OnboardingStatusResponse:
    complete_tenant_onboarding(ctx.tenant_id)
    row = get_onboarding_status(ctx.tenant_id)
    return OnboardingStatusResponse(
        tenant_id=str(row.tenant_id),
        display_name=row.display_name,
        slug=row.slug,
        onboarding_complete=row.onboarding_complete,
        shopify_connected=row.shopify_connected,
    )
