"""Integration health persistence — tenant-scoped (F-CONN-HEALTH)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg

from trita_api.db import database_url


@dataclass(frozen=True)
class IntegrationHealthRow:
    source: str
    status: str
    last_sync_at: datetime | None
    freshness_sla_hours: int
    detail: dict[str, Any] | None
    updated_at: datetime


def _effective_status(
    stored_status: str,
    last_sync_at: datetime | None,
    sla_hours: int,
) -> str:
    """Recompute degraded/failed from SLA when row was marked healthy."""
    if stored_status == "disconnected":
        return stored_status
    if last_sync_at is None:
        return "degraded" if stored_status == "healthy" else stored_status
    age = datetime.now(UTC) - last_sync_at.astimezone(UTC)
    if age > timedelta(hours=sla_hours * 2):
        return "failed"
    if age > timedelta(hours=sla_hours):
        return "degraded"
    return stored_status if stored_status != "disconnected" else "healthy"


def upsert_integration_health(
    *,
    tenant_id: UUID,
    source: str,
    status: str,
    last_sync_at: datetime | None = None,
    detail: dict[str, Any] | None = None,
    freshness_sla_hours: int = 24,
) -> None:
    detail_json = json.dumps(detail) if detail is not None else None
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.integration_health (
                    tenant_id, source, status, last_sync_at,
                    freshness_sla_hours, detail, updated_at
                ) VALUES (%s, %s, %s::public.integration_status, %s, %s, %s::jsonb, now())
                ON CONFLICT (tenant_id, source) DO UPDATE SET
                    status = EXCLUDED.status,
                    last_sync_at = EXCLUDED.last_sync_at,
                    freshness_sla_hours = EXCLUDED.freshness_sla_hours,
                    detail = EXCLUDED.detail,
                    updated_at = now()
                """,
                (
                    tenant_id,
                    source,
                    status,
                    last_sync_at,
                    freshness_sla_hours,
                    detail_json,
                ),
            )


def list_integration_health(tenant_id: UUID) -> list[IntegrationHealthRow]:
    with psycopg.connect(database_url(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, status::text, last_sync_at, freshness_sla_hours, detail, updated_at
                FROM public.integration_health
                WHERE tenant_id = %s
                ORDER BY source
                """,
                (tenant_id,),
            )
            rows = cur.fetchall()

    out: list[IntegrationHealthRow] = []
    for source, status, last_sync_at, sla, detail, updated_at in rows:
        effective = _effective_status(status, last_sync_at, sla)
        parsed_detail = detail if isinstance(detail, dict) else None
        out.append(
            IntegrationHealthRow(
                source=source,
                status=effective,
                last_sync_at=last_sync_at,
                freshness_sla_hours=sla,
                detail=parsed_detail,
                updated_at=updated_at,
            )
        )
    return out
