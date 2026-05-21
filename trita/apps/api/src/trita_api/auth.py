"""JWT tenant context — tenant_id from token only (VA-01)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError

TENANT_CLAIM = "tenant_id"
ROLE_CLAIM = "role"


@dataclass(frozen=True)
class TenantContext:
    user_id: UUID
    tenant_id: UUID
    role: str


def _jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT verification not configured",
        )
    return secret


def decode_access_token(token: str) -> TenantContext:
    """Validate Supabase-style HS256 JWT; require sub + tenant_id claims."""
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", TENANT_CLAIM, "exp"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    try:
        user_id = UUID(str(payload["sub"]))
        tenant_id = UUID(str(payload[TENANT_CLAIM]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        ) from exc

    role = str(payload.get(ROLE_CLAIM, "member"))
    return TenantContext(user_id=user_id, tenant_id=tenant_id, role=role)


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    return header.split(" ", 1)[1].strip()


async def get_tenant_context(request: Request) -> TenantContext:
    token = _bearer_token(request)
    return decode_access_token(token)


TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


def reject_tenant_override(body_tenant_id: UUID | None, ctx: TenantContext) -> None:
    if body_tenant_id is not None and body_tenant_id != ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_id must come from JWT only",
        )
