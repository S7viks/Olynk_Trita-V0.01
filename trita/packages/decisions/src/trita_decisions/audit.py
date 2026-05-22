"""Immutable decision audit log (F-DEC-005)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

REJECT_REASONS = frozenset(
    {
        "wrong_qty",
        "wrong_sku_mapping",
        "already_ordered",
        "supplier_issue",
        "promo_planned",
        "data_stale",
        "not_actionable",
        "other",
    }
)

AUDIT_ACTIONS = frozenset(
    {"emitted", "viewed", "approved", "rejected", "snoozed", "draft_created"}
)


def append_audit(
    cur,
    *,
    tenant_id: UUID,
    decision_id: UUID,
    user_id: UUID,
    action: str,
    projection_hash: str,
    reason_enum: str | None = None,
    reason_text: str | None = None,
) -> UUID:
    if action not in AUDIT_ACTIONS:
        raise ValueError(f"invalid audit action: {action}")
    if reason_enum is not None and reason_enum not in REJECT_REASONS:
        raise ValueError(f"invalid reject reason: {reason_enum}")

    cur.execute(
        """
        INSERT INTO public.decision_audit (
            tenant_id, decision_id, user_id, action,
            reason_enum, reason_text, projection_hash
        ) VALUES (
            %s, %s, %s, %s::public.decision_audit_action,
            %s::public.decision_reject_reason, %s, %s
        )
        RETURNING id
        """,
        (
            tenant_id,
            decision_id,
            user_id,
            action,
            reason_enum,
            reason_text,
            projection_hash,
        ),
    )
    row = cur.fetchone()
    assert row is not None
    return UUID(str(row[0]))


def list_audit_timeline(
    cur,
    tenant_id: UUID,
    decision_id: UUID,
) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, user_id, action::text, reason_enum::text, reason_text,
               projection_hash, created_at
        FROM public.decision_audit
        WHERE tenant_id = %s AND decision_id = %s
        ORDER BY created_at ASC
        """,
        (tenant_id, decision_id),
    )
    return [
        {
            "id": str(r[0]),
            "user_id": str(r[1]),
            "action": r[2],
            "reason_enum": r[3],
            "reason_text": r[4],
            "projection_hash": r[5],
            "timestamp": r[6].isoformat() if r[6] else None,
        }
        for r in cur.fetchall()
    ]
