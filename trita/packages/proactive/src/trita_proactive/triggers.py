"""Trigger evaluation (F-PROACTIVE-001)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_proactive.feed import insert_feed_event


def _trigger_cover(cur, tenant_id: UUID) -> int:
    cur.execute(
        """
        SELECT canonical_sku_id, sku_code, days_of_cover, lead_time_days
        FROM feat.sku_metrics_daily
        WHERE tenant_id = %s
          AND metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
          AND stockout_risk = true
          AND days_of_cover IS NOT NULL
          AND days_of_cover < lead_time_days * 1.2
        """,
        (tenant_id, tenant_id),
    )
    n = 0
    for sku_id, sku_code, cover, lead in cur.fetchall():
        if insert_feed_event(
            cur,
            tenant_id=tenant_id,
            trigger_id="TR-COVER",
            severity="highlight",
            title=f"Cover below lead time — {sku_code}",
            body=(
                f"SKU {sku_code}: cover {float(cover):.1f}d vs lead time "
                f"{float(lead):.0f}d. Review reorder in Inbox."
            ),
            dedup_key=str(sku_id),
            payload={"sku_id": str(sku_id), "sku_code": sku_code, "days_of_cover": float(cover)},
        ):
            n += 1
    return n


def _trigger_vel_delta(cur, tenant_id: UUID) -> int:
    cur.execute(
        """
        SELECT canonical_sku_id, sku_code, velocity_7d, velocity_30d
        FROM feat.sku_metrics_daily
        WHERE tenant_id = %s
          AND metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
          AND velocity_30d > 0
          AND velocity_7d < velocity_30d * 0.6
        """,
        (tenant_id, tenant_id),
    )
    n = 0
    for sku_id, sku_code, v7, v30 in cur.fetchall():
        if insert_feed_event(
            cur,
            tenant_id=tenant_id,
            trigger_id="TR-VEL-DELTA",
            severity="highlight",
            title=f"Velocity down >40% — {sku_code}",
            body=(
                f"7d velocity {float(v7):.2f}/d vs 30d baseline {float(v30):.2f}/d for {sku_code}."
            ),
            dedup_key=str(sku_id),
            payload={"sku_id": str(sku_id), "velocity_7d": float(v7), "velocity_30d": float(v30)},
        ):
            n += 1
    return n


def _trigger_causal(cur, tenant_id: UUID) -> int:
    cur.execute(
        """
        SELECT sku_id, epistemic_layer, cause_variable, effect_variable, narrative
        FROM analytics.causal_edges
        WHERE tenant_id = %s
          AND epistemic_layer IN ('L2', 'L3')
          AND promoted_at >= now() - interval '7 days'
        """,
        (tenant_id,),
    )
    n = 0
    for sku_id, layer, cause, effect, narrative in cur.fetchall():
        if insert_feed_event(
            cur,
            tenant_id=tenant_id,
            trigger_id="TR-CAUSAL",
            severity="info",
            title=f"Causal driver ({layer}) — {sku_id[:8]}…",
            body=narrative or f"{cause} → {effect} ({layer})",
            dedup_key=f"{sku_id}:{layer}:{cause}:{effect}",
            payload={"sku_id": sku_id, "layer": layer},
        ):
            n += 1
    return n


def _trigger_sync_fail(cur, tenant_id: UUID, source: str | None) -> int:
    if not source:
        return 0
    if insert_feed_event(
        cur,
        tenant_id=tenant_id,
        trigger_id="TR-SYNC-FAIL",
        severity="alert",
        title=f"Integration stale — {source}",
        body=f"{source} is past freshness SLA. Inventory decisions suppressed until sync recovers.",
        dedup_key=source,
        payload={"source": source},
    ):
        return 1
    return 0


def evaluate_triggers(
    cur,
    tenant_id: UUID,
    *,
    integrity_source: str | None = None,
) -> dict[str, int]:
    return {
        "TR-COVER": _trigger_cover(cur, tenant_id),
        "TR-VEL-DELTA": _trigger_vel_delta(cur, tenant_id),
        "TR-CAUSAL": _trigger_causal(cur, tenant_id),
        "TR-SYNC-FAIL": _trigger_sync_fail(cur, tenant_id, integrity_source),
    }
