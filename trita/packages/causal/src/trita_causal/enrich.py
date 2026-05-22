"""Attach causal drivers to decision cards (F-CAUSAL-003)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_causal.db import load_best_edge_for_sku
from trita_causal.labels import causal_chain_entry, narrative_for_edge
from trita_causal.types import (
    CausalEdgeResult,
    EvidenceType,
    RefutationStatus,
    layer_rank,
)


def _edge_from_row(tenant_id: UUID, sku_id: str, row: dict[str, Any]) -> CausalEdgeResult:
    return CausalEdgeResult(
        tenant_id=tenant_id,
        sku_id=sku_id,
        cause_variable=str(row["cause_variable"]),
        effect_variable=str(row["effect_variable"]),
        evidence_type=EvidenceType(row["evidence_type"]),
        epistemic_layer=str(row["epistemic_layer"]),
        lag_days=int(row["lag_days"]),
        correlation=row.get("correlation"),
        confidence=row.get("confidence"),
        refutation_status=RefutationStatus(row["refutation_status"]),
        refutation_details=row.get("refutation_details") or {},
        narrative=str(row.get("narrative") or ""),
    )


def enrich_card_from_db(
    cur,
    *,
    tenant_id: UUID,
    sku_id: str,
    card: dict[str, Any],
) -> dict[str, Any]:
    """Merge best causal edge into card reasoning; never L3 without pass."""
    row = load_best_edge_for_sku(cur, tenant_id, sku_id)
    if not row:
        return card

    edge = _edge_from_row(tenant_id, sku_id, row)
    if edge.epistemic_layer == "L3" and edge.refutation_status != RefutationStatus.PASS:
        edge.epistemic_layer = "L2"
        edge.evidence_type = EvidenceType.CAUSAL_CANDIDATE

    if not edge.narrative:
        edge.narrative = narrative_for_edge(edge)

    reasoning = dict(card.get("reasoning") or {})
    chain = list(reasoning.get("causal_chain") or [])
    chain.append(causal_chain_entry(edge, edge_id=row["id"]))
    refs = list(reasoning.get("evidence_refs") or [])
    ref = edge.evidence_ref(row["id"])
    if ref not in refs:
        refs.append(ref)

    current_layer = str(reasoning.get("epistemic_layer", "L0"))
    new_layer = edge.epistemic_layer if layer_rank(edge.epistemic_layer) > layer_rank(current_layer) else current_layer

    reasoning["causal_chain"] = chain
    reasoning["evidence_refs"] = refs
    reasoning["epistemic_layer"] = new_layer
    reasoning["causal_narrative"] = edge.narrative
    card["reasoning"] = reasoning
    return card


def enrich_candidate_card(cur, candidate: Any) -> Any:
    """Enrich EmitCandidate.card in place."""
    card = candidate.card
    enriched = enrich_card_from_db(
        cur,
        tenant_id=candidate.snapshot.tenant_id,
        sku_id=candidate.sku_id,
        card=card,
    )
    candidate.card.update(enriched)  # type: ignore[attr-defined]
    return candidate
