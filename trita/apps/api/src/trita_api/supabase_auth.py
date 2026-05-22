"""Verify Supabase user access tokens (HS256 legacy or asymmetric signing keys)."""

from __future__ import annotations

import os
from uuid import UUID

import httpx
import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError

AUDIENCE = "authenticated"


def _project_url() -> str | None:
    raw = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    return raw.rstrip("/") if raw else None


def _publishable_key() -> str | None:
    return (
        os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
        or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )


def _legacy_jwt_secret() -> str | None:
    """HS256 signing secret from Dashboard → API → JWT Settings (not sb_secret_* API keys)."""
    for name in ("SUPABASE_JWT_SECRET", "API_JWT_SECRET"):
        value = os.environ.get(name, "").strip()
        if value and not value.startswith("sb_"):
            return value
    return None


def _decode_hs256(token: str, secret: str) -> tuple[UUID, str | None]:
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience=AUDIENCE,
        options={"require": ["sub", "exp"]},
    )
    user_id = UUID(str(payload["sub"]))
    email = payload.get("email")
    return user_id, str(email).strip().lower() if email else None


def _verify_via_auth_server(token: str) -> tuple[UUID, str | None]:
    base = _project_url()
    key = _publishable_key()
    if not base or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase URL and publishable key required for token verification",
        )
    try:
        response = httpx.get(
            f"{base}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": key},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Supabase Auth",
        ) from exc
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase token",
        )
    data = response.json()
    try:
        user_id = UUID(str(data["id"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase Auth returned an invalid user payload",
        ) from exc
    email = data.get("email")
    return user_id, str(email).strip().lower() if email else None


def resolve_supabase_user(token: str) -> tuple[UUID, str | None]:
    """
    Resolve Supabase user id + email from a user access token.

    Prefer Auth server verification when project URL + publishable key exist
    (works with ES256 and HS256 signing keys). Fall back to local HS256 when a
    legacy JWT secret is configured (unit tests, air-gapped dev).
    """
    secret = _legacy_jwt_secret()
    if secret:
        try:
            return _decode_hs256(token, secret)
        except InvalidTokenError:
            pass

    base = _project_url()
    key = _publishable_key()
    if base and key:
        return _verify_via_auth_server(token)

    if secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase token",
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Configure TRITA_JWT_SECRET, or SUPABASE_URL + publishable key",
    )
