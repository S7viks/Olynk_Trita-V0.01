"""Proactive feed persistence (F-PROACTIVE-001)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID


def insert_feed_event(
    cur,
    *,
    tenant_id: UUID,
    trigger_id: str,
    severity: str,
    title: str,
    body: str,
    dedup_key: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    cur.execute(
        """
        INSERT INTO public.proactive_feed_events (
            tenant_id, trigger_id, severity, title, body, dedup_key, payload
        ) VALUES (
            %s, %s, %s::public.proactive_severity, %s, %s, %s, %s::jsonb
        )
        ON CONFLICT (tenant_id, trigger_id, dedup_key) DO NOTHING
        RETURNING id
        """,
        (
            tenant_id,
            trigger_id,
            severity,
            title,
            body,
            dedup_key,
            json.dumps(payload or {}),
        ),
    )
    return cur.fetchone() is not None


def list_feed(cur, tenant_id: UUID, *, limit: int = 50) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, trigger_id, severity::text, title, body, payload, created_at
        FROM public.proactive_feed_events
        WHERE tenant_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (tenant_id, limit),
    )
    return [
        {
            "id": str(r[0]),
            "trigger_id": r[1],
            "severity": r[2],
            "title": r[3],
            "body": r[4],
            "payload": r[5] or {},
            "created_at": r[6].isoformat() if r[6] else None,
        }
        for r in cur.fetchall()
    ]
