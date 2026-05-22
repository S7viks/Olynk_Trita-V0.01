"""ContextProjection from graph tables (F-CHAT-001) — no LLM numbers."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

_SKU_CODE = re.compile(r"\b([A-Z]{1,4}-[A-Z0-9]{2,8})\b")
_SKU_ID = re.compile(r"\b([a-f0-9]{32})\b", re.I)


def resolve_sku_hint(message: str) -> str | None:
    m = _SKU_CODE.search(message)
    if m:
        return m.group(1)
    m = _SKU_ID.search(message)
    if m:
        return m.group(1)
    return None


def build_context_projection(
    cur,
    tenant_id: UUID,
    *,
    sku_hint: str | None = None,
) -> dict[str, Any]:
    evidence_refs: list[str] = []
    blocks: list[str] = []

    cur.execute(
        """
        SELECT source, status::text, last_sync_at
        FROM public.integration_health
        WHERE tenant_id = %s
        ORDER BY source
        """,
        (tenant_id,),
    )
    health_rows = cur.fetchall()
    if health_rows:
        parts = [f"{r[0]}={r[1]}" for r in health_rows]
        blocks.append("Integration health: " + ", ".join(parts))
        evidence_refs.append("public.integration_health:latest")

    cur.execute(
        """
        SELECT count(*) FILTER (WHERE stockout_risk),
               count(*) FILTER (WHERE dead_stock),
               max(metric_date)
        FROM feat.sku_metrics_daily
        WHERE tenant_id = %s
          AND metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
        """,
        (tenant_id, tenant_id),
    )
    stockout_n, dead_n, metric_date = cur.fetchone()
    if metric_date:
        blocks.append(
            f"Tenant metrics ({metric_date}): {int(stockout_n or 0)} stockout-risk SKUs, "
            f"{int(dead_n or 0)} dead-stock SKUs."
        )
        evidence_refs.append(f"feat.sku_metrics_daily:{metric_date}:summary")

    sku_row = None
    if sku_hint:
        cur.execute(
            """
            SELECT canonical_sku_id, sku_code, on_hand, velocity_7d, days_of_cover,
                   stockout_risk, dead_stock, cogs_missing
            FROM feat.sku_metrics_daily
            WHERE tenant_id = %s
              AND metric_date = (
                  SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
              )
              AND (sku_code ILIKE %s OR canonical_sku_id = %s)
            LIMIT 1
            """,
            (tenant_id, tenant_id, sku_hint, sku_hint),
        )
        sku_row = cur.fetchone()

    if sku_row:
        sid, code, on_hand, v7, cover, stockout, dead, cogs_miss = sku_row
        blocks.append(
            f"SKU {code}: on_hand={float(on_hand or 0):.0f}, "
            f"velocity_7d={float(v7 or 0):.2f}, cover_days="
            f"{'' if cover is None else f'{float(cover):.1f}'}, "
            f"stockout_risk={bool(stockout)}, dead_stock={bool(dead)}, "
            f"cogs_missing={bool(cogs_miss)}."
        )
        evidence_refs.append(f"feat.sku_metrics_daily:{metric_date}:{sid}")

        cur.execute(
            """
            SELECT id, decision_type::text, status::text, inr_floor
            FROM public.decisions
            WHERE tenant_id = %s AND sku_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id, str(sid)),
        )
        dec = cur.fetchone()
        if dec:
            blocks.append(
                f"Latest decision: {dec[1]} ({dec[2]}), floor ₹{float(dec[3]):,.0f}."
            )
            evidence_refs.append(f"public.decisions:{dec[0]}")

        cur.execute(
            """
            SELECT epistemic_layer, narrative
            FROM analytics.causal_edges
            WHERE tenant_id = %s AND sku_id = %s
            ORDER BY CASE epistemic_layer WHEN 'L3' THEN 3 WHEN 'L2' THEN 2 ELSE 1 END DESC
            LIMIT 1
            """,
            (tenant_id, str(sid)),
        )
        causal = cur.fetchone()
        if causal:
            blocks.append(f"Causal ({causal[0]}): {causal[1]}")
            evidence_refs.append(f"analytics.causal_edges:{sid}")

    return {
        "sku_resolved": sku_row is not None,
        "sku_hint": sku_hint,
        "blocks": blocks,
        "evidence_refs": evidence_refs,
    }
