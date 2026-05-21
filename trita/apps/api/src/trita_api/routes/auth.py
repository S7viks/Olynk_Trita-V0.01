"""Exchange Supabase user JWT for tenant-scoped API token (T-P0-040)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from trita_api.auth import ROLE_CLAIM, TENANT_CLAIM, _bearer_token, _jwt_secret
from trita_api.db import get_primary_membership

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class ExchangeResponse(BaseModel):
    access_token: str
    tenant_id: str
    tenant_slug: str | None
    role: str
    expires_in: int


def _decode_user_id(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase token",
        ) from exc
    try:
        return UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        ) from exc


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


@router.post("/exchange", response_model=ExchangeResponse)
def auth_exchange(request: Request) -> ExchangeResponse:
    """Map authenticated Supabase user → tenant-scoped JWT (tenant_id from membership)."""
    supabase_token = _bearer_token(request)
    user_id = _decode_user_id(supabase_token)
    membership = get_primary_membership(user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant membership for this user",
        )
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
    )
