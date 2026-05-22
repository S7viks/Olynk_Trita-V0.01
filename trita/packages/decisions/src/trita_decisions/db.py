"""Persist decisions (tenant-scoped)."""

from __future__ import annotations

import json
from uuid import UUID

from trita_decisions.candidates import EmitCandidate
from trita_decisions.contract import DecisionType


def insert_decision(cur, candidate: EmitCandidate) -> bool:
    """Insert card; returns False on suppression_key conflict."""
    card = candidate.card
    cur.execute(
        """
        INSERT INTO public.decisions (
            id, tenant_id, decision_type, sku_id, event, status,
            suppression_key, projection_hash, inr_floor, card
        ) VALUES (
            %s::uuid, %s, %s::public.decision_type, %s, %s,
            'open'::public.decision_status,
            %s, %s, %s, %s::jsonb
        )
        ON CONFLICT (tenant_id, suppression_key) DO NOTHING
        RETURNING id
        """,
        (
            card["id"],
            candidate.snapshot.tenant_id,
            candidate.decision_type.value,
            candidate.sku_id,
            candidate.event,
            candidate.suppression,
            candidate.projection,
            candidate.inr_floor,
            json.dumps(card),
        ),
    )
    return cur.fetchone() is not None


def list_decisions(
    cur,
    tenant_id: UUID,
    *,
    status: str | None = "open",
    limit: int = 50,
) -> list[dict[str, object]]:
    clauses = ["tenant_id = %s"]
    params: list[object] = [tenant_id]
    if status:
        clauses.append("status = %s::public.decision_status")
        params.append(status)
    where_sql = " AND ".join(clauses)
    params.append(limit)
    cur.execute(
        f"""
        SELECT id, decision_type::text, sku_id, event, status::text,
               suppression_key, inr_floor, card, created_at
        FROM public.decisions
        WHERE {where_sql}
        ORDER BY inr_floor DESC NULLS LAST, created_at DESC
        LIMIT %s
        """,
        params,
    )
    rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "type": r[1],
            "sku_id": r[2],
            "event": r[3],
            "status": r[4],
            "suppression_key": r[5],
            "inr_floor": float(r[6]),
            "card": r[7],
            "created_at": r[8].isoformat() if r[8] else None,
        }
        for r in rows
    ]
