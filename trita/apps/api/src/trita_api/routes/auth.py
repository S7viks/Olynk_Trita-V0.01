"""Exchange Supabase user JWT for tenant-scoped API token (T-P0-040)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from trita_api.auth import ROLE_CLAIM, TENANT_CLAIM, _bearer_token, _jwt_secret
from trita_api.supabase_auth import resolve_supabase_user
from trita_api.db import (
    get_onboarding_status,
    get_primary_membership,
    provision_tenant_for_user,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class ExchangeResponse(BaseModel):
    access_token: str
    tenant_id: str
    tenant_slug: str | None
    role: str
    expires_in: int
    onboarding_complete: bool


class RegisterBody(BaseModel):
    company_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None


class RegisterResponse(BaseModel):
    tenant_id: str
    tenant_slug: str
    display_name: str
    role: str


def _decode_user_id(token: str) -> UUID:
    user_id, _ = resolve_supabase_user(token)
    return user_id


def _decode_user_email(token: str) -> str | None:
    _, email = resolve_supabase_user(token)
    return email


def _mint_tenant_token(*, user_id: UUID, tenant_id: UUID, role: str) -> tuple[str, int]:
    expires_in = 8 * 3600
    exp = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        TENANT_CLAIM: str(tenant_id),
        ROLE_CLAIM: role,
        "aud": "authenticated",
        "exp": exp,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm="HS256")
    return token, expires_in


def _exchange_response(membership, user_id: UUID) -> ExchangeResponse:
    onboarding = get_onboarding_status(membership.tenant_id)
    access_token, expires_in = _mint_tenant_token(
        user_id=user_id,
        tenant_id=membership.tenant_id,
        role=membership.role,
    )
    return ExchangeResponse(
        access_token=access_token,
        tenant_id=str(membership.tenant_id),
        tenant_slug=membership.tenant_slug,
        role=membership.role,
        expires_in=expires_in,
        onboarding_complete=onboarding.onboarding_complete,
    )


@router.post("/register", response_model=RegisterResponse)
def auth_register(request: Request, body: RegisterBody) -> RegisterResponse:
    """Provision tenant + owner membership for a new Supabase user (email or Google)."""
    supabase_token = _bearer_token(request)
    user_id = _decode_user_id(supabase_token)
    existing = get_primary_membership(user_id)
    if existing:
        onboarding = get_onboarding_status(existing.tenant_id)
        return RegisterResponse(
            tenant_id=str(existing.tenant_id),
            tenant_slug=existing.tenant_slug or "",
            display_name=onboarding.display_name,
            role=existing.role,
        )

    email = (body.email or _decode_user_email(supabase_token) or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email required in token or request body",
        )

    membership = provision_tenant_for_user(
        user_id=user_id,
        email=email,
        display_name=body.company_name,
    )
    onboarding = get_onboarding_status(membership.tenant_id)
    return RegisterResponse(
        tenant_id=str(membership.tenant_id),
        tenant_slug=membership.tenant_slug or "",
        display_name=onboarding.display_name,
        role=membership.role,
    )


@router.post("/exchange", response_model=ExchangeResponse)
def auth_exchange(request: Request) -> ExchangeResponse:
    """Map authenticated Supabase user → tenant-scoped JWT (tenant_id from membership)."""
    supabase_token = _bearer_token(request)
    user_id = _decode_user_id(supabase_token)
    membership = get_primary_membership(user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant membership — call POST /v1/auth/register first",
        )
    return _exchange_response(membership, user_id)
