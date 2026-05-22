"""Development-only API token mint for local web (ENVIRONMENT=development)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/dev/auth", tags=["dev"])


def _dev_only() -> None:
    if os.environ.get("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="dev only")


def _jwt_secret() -> str:
    from trita_api.auth import _jwt_secret as trita_secret

    return trita_secret()


class DevTokenResponse(BaseModel):
    access_token: str
    tenant_id: str
    expires_in: int


@router.post("/token", response_model=DevTokenResponse)
def dev_mint_token() -> DevTokenResponse:
    """Mint tenant-scoped JWT for Yoga Bar pilot (local web only)."""
    _dev_only()
    raw = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOGA_BAR_TENANT_ID not set in .env",
        )
    try:
        tenant_id = UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOGA_BAR_TENANT_ID must be a UUID",
        ) from exc

    exp = datetime.now(UTC) + timedelta(hours=8)
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "tenant_id": str(tenant_id),
        "role": "owner",
        "aud": "authenticated",
        "exp": exp,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm="HS256")
    return DevTokenResponse(
        access_token=token,
        tenant_id=str(tenant_id),
        expires_in=8 * 3600,
    )
