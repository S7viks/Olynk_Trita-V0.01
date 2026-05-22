"""Deterministic card copy — no LLM qty/cover/₹ (F-CAUSAL-003)."""

from __future__ import annotations

from trita_causal.types import CausalEdgeResult


def l1_label(edge: CausalEdgeResult) -> str:
    r = edge.correlation
    r_txt = f"{r:.2f}" if r is not None else "n/a"
    cause = _human(edge.cause_variable)
    effect = _human(edge.effect_variable)
    lag = edge.lag_days
    return f"Correlated with {cause} (lag {lag}d, r={r_txt}) — not a causal claim"


def l2_label(edge: CausalEdgeResult) -> str:
    return (
        f"Hypothesis: {_human(edge.cause_variable)} may be affecting "
        f"{_human(edge.effect_variable)} (refutation pending or incomplete)"
    )


def l3_label(edge: CausalEdgeResult) -> str:
    if edge.refutation_status.value != "pass":
        raise ValueError("L3 label requires refutation_status pass (VA-18)")
    return (
        f"Tested driver: {_human(edge.cause_variable)} → {_human(edge.effect_variable)} "
        f"(lag {edge.lag_days}d, passed refutation)"
    )


def narrative_for_edge(edge: CausalEdgeResult) -> str:
    if edge.epistemic_layer == "L3":
        return l3_label(edge)
    if edge.epistemic_layer == "L2":
        return l2_label(edge)
    return l1_label(edge)


def causal_chain_entry(edge: CausalEdgeResult, *, edge_id: str | None = None) -> dict[str, object]:
    ref = edge.evidence_ref(edge_id) if edge_id else None
    return {
        "layer": edge.epistemic_layer,
        "label": narrative_for_edge(edge),
        "cause": edge.cause_variable,
        "effect": edge.effect_variable,
        "lag_days": edge.lag_days,
        "correlation": edge.correlation,
        "evidence_type": edge.evidence_type.value,
        "refutation_status": edge.refutation_status.value,
        "evidence_ref": ref,
    }


def _human(var: str) -> str:
    return var.replace("_", " ")
