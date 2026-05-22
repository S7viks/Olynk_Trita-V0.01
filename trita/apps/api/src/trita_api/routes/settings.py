"""Tenant notification settings (F-SETTINGS-001)."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from trita_api.auth import TenantDep
from trita_api.db import database_url

router = APIRouter(prefix="/v1/settings", tags=["settings"])


class NotificationSettingsBody(BaseModel):
    email_to: str | None = None
    weekly_digest_enabled: bool | None = None
    urgent_enabled: bool | None = None


def _row_to_dict(row: tuple) -> dict[str, object]:
    return {
        "tenant_id": str(row[0]),
        "weekly_digest_enabled": bool(row[1]),
        "urgent_enabled": bool(row[2]),
        "email_to": row[3],
        "updated_at": row[4].isoformat() if row[4] else None,
    }


def _ensure_row(cur: psycopg.Cursor, tenant_id: object) -> None:
    cur.execute(
        """
        INSERT INTO public.notification_settings (
            tenant_id, weekly_digest_enabled, urgent_enabled, email_to
        ) VALUES (%s, true, true, NULL)
        ON CONFLICT (tenant_id) DO NOTHING
        """,
        (tenant_id,),
    )


@router.get("/notifications")
def get_notification_settings(ctx: TenantDep) -> dict[str, object]:
    sql = """
        SELECT tenant_id, weekly_digest_enabled, urgent_enabled, email_to, updated_at
        FROM public.notification_settings
        WHERE tenant_id = %s
    """
    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                _ensure_row(cur, ctx.tenant_id)
                cur.execute(sql, (ctx.tenant_id,))
                row = cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Settings unavailable: {exc}",
        ) from exc

    if not row:
        return {
            "tenant_id": str(ctx.tenant_id),
            "weekly_digest_enabled": True,
            "urgent_enabled": True,
            "email_to": None,
            "updated_at": None,
        }
    return _row_to_dict(row)


@router.patch("/notifications")
def patch_notification_settings(
    body: NotificationSettingsBody,
    ctx: TenantDep,
) -> dict[str, object]:
    fields: list[str] = []
    params: list[object] = []
    if body.email_to is not None:
        fields.append("email_to = %s")
        params.append(body.email_to.strip() or None)
    if body.weekly_digest_enabled is not None:
        fields.append("weekly_digest_enabled = %s")
        params.append(body.weekly_digest_enabled)
    if body.urgent_enabled is not None:
        fields.append("urgent_enabled = %s")
        params.append(body.urgent_enabled)

    if not fields:
        return get_notification_settings(ctx)

    fields.append("updated_at = now()")
    params.append(ctx.tenant_id)
    sql = f"""
        UPDATE public.notification_settings
        SET {", ".join(fields)}
        WHERE tenant_id = %s
        RETURNING tenant_id, weekly_digest_enabled, urgent_enabled, email_to, updated_at
    """
    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                _ensure_row(cur, ctx.tenant_id)
                cur.execute(sql, params)
                row = cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Settings update failed: {exc}",
        ) from exc

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return _row_to_dict(row)
