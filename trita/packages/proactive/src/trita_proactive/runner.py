"""Run proactive triggers for tenant."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_proactive.digest import send_urgent_digest
from trita_proactive.feed import list_feed
from trita_proactive.triggers import evaluate_triggers


def run_proactive_triggers(
    conn,
    tenant_id: UUID,
    *,
    integrity_suppressed: bool = False,
    integrity_source: str | None = None,
) -> dict[str, Any]:
    with conn.cursor() as cur:
        counts = evaluate_triggers(
            cur,
            tenant_id,
            integrity_source=integrity_source if integrity_suppressed else None,
        )
        urgent = None
        if integrity_suppressed and integrity_source:
            urgent = send_urgent_digest(
                cur,
                tenant_id,
                title=f"{integrity_source} sync stale",
                message=(
                    f"Shopify/Unicommerce sync for {integrity_source} is past SLA. "
                    "Open Sources to resync."
                ),
                payload={"trigger": "TR-SYNC-FAIL", "source": integrity_source},
            )
        feed = list_feed(cur, tenant_id, limit=20)
    return {
        "tenant_id": str(tenant_id),
        "triggers": counts,
        "new_events": sum(counts.values()),
        "urgent_digest": urgent,
        "feed_preview_count": len(feed),
    }
