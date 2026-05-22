"""Persist analytics.causal_edges."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from trita_causal.types import CausalEdgeResult


def upsert_edge(cur, edge: CausalEdgeResult) -> UUID:
    row = edge.to_db_row()
    cur.execute(
        """
        INSERT INTO analytics.causal_edges (
            tenant_id, sku_id, cause_variable, effect_variable,
            evidence_type, epistemic_layer, lag_days, correlation, confidence,
            refutation_status, refutation_details, n_weeks, completeness,
            narrative, promoted_at
        ) VALUES (
            %s, %s, %s, %s,
            %s::analytics.causal_evidence_type,
            %s, %s, %s, %s,
            %s::analytics.causal_refutation_status,
            %s::jsonb, %s, %s,
            %s,
            CASE WHEN %s IN ('L2', 'L3') THEN now() ELSE NULL END
        )
        ON CONFLICT (tenant_id, sku_id, cause_variable, effect_variable, lag_days)
        DO UPDATE SET
            evidence_type = EXCLUDED.evidence_type,
            epistemic_layer = EXCLUDED.epistemic_layer,
            correlation = EXCLUDED.correlation,
            confidence = EXCLUDED.confidence,
            refutation_status = EXCLUDED.refutation_status,
            refutation_details = EXCLUDED.refutation_details,
            n_weeks = EXCLUDED.n_weeks,
            completeness = EXCLUDED.completeness,
            narrative = EXCLUDED.narrative,
            promoted_at = EXCLUDED.promoted_at,
            updated_at = now()
        RETURNING id
        """,
        (
            row["tenant_id"],
            row["sku_id"],
            row["cause_variable"],
            row["effect_variable"],
            row["evidence_type"],
            row["epistemic_layer"],
            row["lag_days"],
            row["correlation"],
            row["confidence"],
            row["refutation_status"],
            json.dumps(row["refutation_details"]),
            row["n_weeks"],
            row["completeness"],
            row["narrative"],
            row["epistemic_layer"],
        ),
    )
    inserted = cur.fetchone()
    if not inserted:
        raise RuntimeError("failed to upsert causal edge")
    return UUID(str(inserted[0]))


def load_best_edge_for_sku(cur, tenant_id: UUID, sku_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT
            id, cause_variable, effect_variable, evidence_type::text,
            epistemic_layer, lag_days, correlation, confidence,
            refutation_status::text, refutation_details, narrative
        FROM analytics.causal_edges
        WHERE tenant_id = %s AND sku_id = %s
        ORDER BY
            CASE epistemic_layer
                WHEN 'L3' THEN 3
                WHEN 'L2' THEN 2
                WHEN 'L1' THEN 1
                ELSE 0
            END DESC,
            abs(coalesce(correlation, 0)) DESC
        LIMIT 1
        """,
        (tenant_id, sku_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "cause_variable": row[1],
        "effect_variable": row[2],
        "evidence_type": row[3],
        "epistemic_layer": row[4],
        "lag_days": row[5],
        "correlation": float(row[6]) if row[6] is not None else None,
        "confidence": float(row[7]) if row[7] is not None else None,
        "refutation_status": row[8],
        "refutation_details": row[9] or {},
        "narrative": row[10] or "",
    }
