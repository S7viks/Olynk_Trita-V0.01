"""Inbox actions: approve, reject, snooze (F-INBOX-003, F-DEC-005)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from trita_decisions.audit import REJECT_REASONS, append_audit, list_audit_timeline


def get_decision(cur, tenant_id: UUID, decision_id: UUID) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT id, decision_type::text, sku_id, event, status::text,
               suppression_key, projection_hash, inr_floor, card,
               created_at, snoozed_until
        FROM public.decisions
        WHERE tenant_id = %s AND id = %s
        """,
        (tenant_id, decision_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    card = row[8]
    sku_code = None
    if isinstance(card, dict):
        rec = card.get("recommendation") or {}
        params = rec.get("parameters") or {}
        sku_code = params.get("sku_code")
    return {
        "id": str(row[0]),
        "type": row[1],
        "sku_id": row[2],
        "sku_code": sku_code,
        "event": row[3],
        "status": row[4],
        "suppression_key": row[5],
        "projection_hash": row[6],
        "inr_floor": float(row[7]),
        "card": card,
        "created_at": row[9].isoformat() if row[9] else None,
        "snoozed_until": row[10].isoformat() if row[10] else None,
    }


def list_inbox(
    cur,
    tenant_id: UUID,
    *,
    tab: str = "open",
    limit: int = 50,
) -> list[dict[str, Any]]:
    if tab == "open":
        status_sql = "status = 'open'::public.decision_status"
    elif tab == "snoozed":
        status_sql = "status = 'snoozed'::public.decision_status"
    elif tab == "done":
        status_sql = "status IN ('approved'::public.decision_status, 'rejected'::public.decision_status)"
    else:
        status_sql = "status = 'open'::public.decision_status"

    cur.execute(
        f"""
        SELECT id, decision_type::text, sku_id, event, status::text,
               inr_floor, card, created_at
        FROM public.decisions
        WHERE tenant_id = %s AND {status_sql}
        ORDER BY inr_floor DESC NULLS LAST, created_at DESC
        LIMIT %s
        """,
        (tenant_id, limit),
    )
    items = []
    for r in cur.fetchall():
        card = r[6]
        sku_code = None
        preview = ""
        if isinstance(card, dict):
            rec = card.get("recommendation") or {}
            params = rec.get("parameters") or {}
            sku_code = params.get("sku_code")
            layer = (card.get("reasoning") or {}).get("epistemic_layer", "L0")
            preview = f"{layer} · {card.get('event', r[3])}"
        items.append(
            {
                "id": str(r[0]),
                "type": r[1],
                "sku_id": r[2],
                "sku_code": sku_code,
                "event": r[3],
                "status": r[4],
                "inr_floor": float(r[5]),
                "preview": preview,
                "created_at": r[7].isoformat() if r[7] else None,
            }
        )
    return items


def approve_decision(
    cur,
    *,
    tenant_id: UUID,
    decision_id: UUID,
    user_id: UUID,
) -> dict[str, Any]:
    row = get_decision(cur, tenant_id, decision_id)
    if not row:
        raise LookupError("decision not found")
    if row["status"] != "open":
        raise ValueError(f"cannot approve decision in status {row['status']}")

    cur.execute(
        """
        UPDATE public.decisions
        SET status = 'approved'::public.decision_status, updated_at = now()
        WHERE tenant_id = %s AND id = %s
        """,
        (tenant_id, decision_id),
    )
    append_audit(
        cur,
        tenant_id=tenant_id,
        decision_id=decision_id,
        user_id=user_id,
        action="approved",
        projection_hash=row["projection_hash"],
    )
    return {"decision_id": str(decision_id), "status": "approved"}


def reject_decision(
    cur,
    *,
    tenant_id: UUID,
    decision_id: UUID,
    user_id: UUID,
    reason_enum: str,
    reason_text: str | None = None,
) -> dict[str, Any]:
    if reason_enum not in REJECT_REASONS:
        raise ValueError("reason_enum is required and must be a valid enum value")

    row = get_decision(cur, tenant_id, decision_id)
    if not row:
        raise LookupError("decision not found")
    if row["status"] not in ("open", "snoozed"):
        raise ValueError(f"cannot reject decision in status {row['status']}")

    cur.execute(
        """
        UPDATE public.decisions
        SET status = 'rejected'::public.decision_status, updated_at = now()
        WHERE tenant_id = %s AND id = %s
        """,
        (tenant_id, decision_id),
    )
    append_audit(
        cur,
        tenant_id=tenant_id,
        decision_id=decision_id,
        user_id=user_id,
        action="rejected",
        projection_hash=row["projection_hash"],
        reason_enum=reason_enum,
        reason_text=reason_text,
    )
    return {"decision_id": str(decision_id), "status": "rejected", "reason_enum": reason_enum}


def snooze_decision(
    cur,
    *,
    tenant_id: UUID,
    decision_id: UUID,
    user_id: UUID,
    days: int = 7,
) -> dict[str, Any]:
    if days < 1 or days > 30:
        raise ValueError("days must be between 1 and 30")

    row = get_decision(cur, tenant_id, decision_id)
    if not row:
        raise LookupError("decision not found")
    if row["status"] != "open":
        raise ValueError(f"cannot snooze decision in status {row['status']}")

    until = datetime.now(UTC) + timedelta(days=days)
    cur.execute(
        """
        UPDATE public.decisions
        SET status = 'snoozed'::public.decision_status,
            snoozed_until = %s,
            updated_at = now()
        WHERE tenant_id = %s AND id = %s
        """,
        (until, tenant_id, decision_id),
    )
    append_audit(
        cur,
        tenant_id=tenant_id,
        decision_id=decision_id,
        user_id=user_id,
        action="snoozed",
        projection_hash=row["projection_hash"],
    )
    return {
        "decision_id": str(decision_id),
        "status": "snoozed",
        "snoozed_until": until.isoformat(),
    }


def decision_with_timeline(
    cur,
    tenant_id: UUID,
    decision_id: UUID,
) -> dict[str, Any] | None:
    decision = get_decision(cur, tenant_id, decision_id)
    if not decision:
        return None
    decision["timeline"] = list_audit_timeline(cur, tenant_id, decision_id)
    return decision
