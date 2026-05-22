"""Weekly / urgent digests (F-PROACTIVE-002, F-PROACTIVE-003, F-PROACTIVE-004)."""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any
from uuid import UUID


def _open_decisions(cur, tenant_id: UUID, limit: int = 3) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, decision_type::text, sku_id, inr_floor, card
        FROM public.decisions
        WHERE tenant_id = %s
          AND status = 'open'::public.decision_status
        ORDER BY inr_floor DESC NULLS LAST, created_at DESC
        LIMIT %s
        """,
        (tenant_id, limit),
    )
    items = []
    for row in cur.fetchall():
        card = row[4] if isinstance(row[4], dict) else {}
        rec = (card.get("recommendation") or {}) if isinstance(card, dict) else {}
        params = rec.get("parameters") or {}
        items.append(
            {
                "decision_id": str(row[0]),
                "type": row[1],
                "sku_id": row[2],
                "sku_code": params.get("sku_code"),
                "inr_floor": float(row[3]),
            }
        )
    return items


def _digest_already_sent(
    cur,
    tenant_id: UUID,
    *,
    channel: str,
    digest_kind: str,
    delivery_day: date,
) -> bool:
    cur.execute(
        """
        SELECT 1 FROM public.digest_deliveries
        WHERE tenant_id = %s
          AND channel = %s::public.digest_channel
          AND digest_kind = %s::public.digest_kind
          AND delivery_day = %s
        LIMIT 1
        """,
        (tenant_id, channel, digest_kind, delivery_day),
    )
    return cur.fetchone() is not None


def _record_delivery(
    cur,
    *,
    tenant_id: UUID,
    channel: str,
    digest_kind: str,
    subject: str,
    body: str,
    payload: dict[str, Any],
    delivery_day: date,
) -> UUID | None:
    cur.execute(
        """
        INSERT INTO public.digest_deliveries (
            tenant_id, channel, digest_kind, subject, body, payload, delivery_day
        ) VALUES (
            %s, %s::public.digest_channel, %s::public.digest_kind, %s, %s, %s::jsonb, %s
        )
        RETURNING id
        """,
        (
            tenant_id,
            channel,
            digest_kind,
            subject,
            body,
            json.dumps(payload),
            delivery_day,
        ),
    )
    row = cur.fetchone()
    return UUID(str(row[0])) if row else None


def _maybe_send_email(to: str | None, subject: str, body: str) -> dict[str, Any]:
    """Optional real send when RESEND_API_KEY configured; else log-only."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key or not to:
        return {"sent": False, "reason": "email_not_configured"}
    try:
        import httpx

        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": os.environ.get("DIGEST_FROM_EMAIL", "Trita <digest@olynk.io>"),
                "to": [to],
                "subject": subject,
                "text": body,
            },
            timeout=30.0,
        )
        return {"sent": resp.status_code in (200, 201), "status": resp.status_code}
    except Exception as exc:
        return {"sent": False, "reason": str(exc)}


def send_weekly_digest(cur, tenant_id: UUID) -> dict[str, Any]:
    today = date.today()
    if _digest_already_sent(cur, tenant_id, channel="email", digest_kind="weekly", delivery_day=today):
        return {"skipped": True, "reason": "weekly_already_sent_today"}

    cards = _open_decisions(cur, tenant_id, limit=3)
    lines = [
        "Trita weekly digest — top open inventory decisions",
        "",
    ]
    for i, c in enumerate(cards, start=1):
        lines.append(
            f"{i}. {c.get('sku_code') or c['sku_id']} — {c['type']} "
            f"(₹ floor {c['inr_floor']:,.0f})"
        )
    if not cards:
        lines.append("No open decision cards this week.")
    body = "\n".join(lines)
    subject = "Trita weekly inventory digest"

    cur.execute(
        "SELECT email_to, weekly_digest_enabled FROM public.notification_settings WHERE tenant_id = %s",
        (tenant_id,),
    )
    settings = cur.fetchone()
    email_to = settings[0] if settings else None
    enabled = settings[1] if settings else True
    if enabled is False:
        return {"skipped": True, "reason": "weekly_disabled"}

    payload = {"cards": cards, "card_count": len(cards)}
    delivery_id = _record_delivery(
        cur,
        tenant_id=tenant_id,
        channel="email",
        digest_kind="weekly",
        subject=subject,
        body=body,
        payload=payload,
        delivery_day=today,
    )
    email_result = _maybe_send_email(email_to, subject, body)
    _record_delivery(
        cur,
        tenant_id=tenant_id,
        channel="slack",
        digest_kind="weekly",
        subject=subject,
        body=body,
        payload={**payload, "mirror": "slack", "email_result": email_result},
        delivery_day=today,
    )
    return {
        "delivery_id": str(delivery_id) if delivery_id else None,
        "channel": "email",
        "digest_kind": "weekly",
        "cards": len(cards),
        "email": email_result,
    }


def send_urgent_digest(
    cur,
    tenant_id: UUID,
    *,
    title: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    today = date.today()
    if _digest_already_sent(cur, tenant_id, channel="email", digest_kind="urgent", delivery_day=today):
        return {"skipped": True, "reason": "urgent_cap_reached"}

    subject = f"Trita urgent: {title}"
    body = message
    cur.execute(
        "SELECT email_to, urgent_enabled FROM public.notification_settings WHERE tenant_id = %s",
        (tenant_id,),
    )
    settings = cur.fetchone()
    email_to = settings[0] if settings else None
    enabled = settings[1] if settings else True
    if enabled is False:
        return {"skipped": True, "reason": "urgent_disabled"}

    pl = payload or {}
    delivery_id = _record_delivery(
        cur,
        tenant_id=tenant_id,
        channel="email",
        digest_kind="urgent",
        subject=subject,
        body=body,
        payload=pl,
        delivery_day=today,
    )
    email_result = _maybe_send_email(email_to, subject, body)
    return {
        "delivery_id": str(delivery_id) if delivery_id else None,
        "digest_kind": "urgent",
        "email": email_result,
    }
