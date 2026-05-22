"""Integrity suppress — stale Shopify or Unicommerce blocks emit (F-DEC-003)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg

INTEGRITY_SOURCES = ("shopify", "unicommerce")


@dataclass(frozen=True)
class HealthSnapshot:
    source: str
    status: str
    last_sync_at: datetime | None
    freshness_sla_hours: int


def _effective_status(stored: str, last_sync_at: datetime | None, sla_hours: int) -> str:
    if stored == "disconnected":
        return stored
    if last_sync_at is None:
        return "degraded" if stored == "healthy" else stored
    age = datetime.now(UTC) - last_sync_at.astimezone(UTC)
    if age > timedelta(hours=sla_hours * 2):
        return "failed"
    if age > timedelta(hours=sla_hours):
        return "degraded"
    return stored if stored != "disconnected" else "healthy"


def load_health_snapshots(cur, tenant_id: UUID) -> list[HealthSnapshot]:
    cur.execute(
        """
        SELECT source, status::text, last_sync_at, freshness_sla_hours
        FROM public.integration_health
        WHERE tenant_id = %s AND source = ANY(%s)
        """,
        (tenant_id, list(INTEGRITY_SOURCES)),
    )
    out: list[HealthSnapshot] = []
    for source, status, last_sync_at, sla in cur.fetchall():
        effective = _effective_status(status, last_sync_at, sla)
        out.append(
            HealthSnapshot(
                source=source,
                status=effective,
                last_sync_at=last_sync_at,
                freshness_sla_hours=sla,
            )
        )
    return out


def integrity_suppresses(snapshots: list[HealthSnapshot]) -> tuple[bool, str | None]:
    """True when a connected source is past SLA (degraded/failed)."""
    for row in snapshots:
        if row.status == "disconnected":
            continue
        if row.status in ("degraded", "failed"):
            return True, row.source
    return False, None


def check_integrity_suppress(cur, tenant_id: UUID) -> tuple[bool, str | None]:
    return integrity_suppresses(load_health_snapshots(cur, tenant_id))
