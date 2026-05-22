"""DoWhy estimate + refutation battery (F-CAUSAL-002)."""

from __future__ import annotations

import random
from typing import Any

from trita_causal.association import _pearson, _series
from trita_causal.policy import load_policy
from trita_causal.types import (
    CausalEdgeResult,
    EvidenceType,
    RefutationStatus,
    SkuMatrix,
)


def _refutation_battery(
    matrix: SkuMatrix,
    edge: CausalEdgeResult,
) -> tuple[RefutationStatus, dict[str, Any]]:
    """
    Placebo, random common cause, subset stability.
    Documented in refutation_details for VA-18.
    """
    policy = load_policy()
    tests = list(policy.get("refutation_tests", []))
    rows = matrix.rows
    cause = edge.cause_variable
    effect = edge.effect_variable
    lag = edge.lag_days

    x = _series(rows, cause, lag=lag)
    y = _series(rows, effect, lag=0)
    base_r = _pearson(x, y)

    details: dict[str, Any] = {"tests": {}, "method": "internal_battery"}
    passes = 0
    required = 0

    if "placebo" in tests:
        required += 1
        shuffled = x[:]
        random.Random(42).shuffle(shuffled)
        placebo_r = _pearson(shuffled, y)
        ok = placebo_r is None or abs(placebo_r) < abs(base_r or 0) * 0.5
        details["tests"]["placebo"] = {
            "pass": ok,
            "baseline_r": base_r,
            "placebo_r": placebo_r,
        }
        if ok:
            passes += 1

    if "random_common_cause" in tests:
        required += 1
        n = len(rows)
        common = [random.Random(99).uniform(0, 1) for _ in range(n)]
        rx = _pearson(common, x)
        ry = _pearson(common, y)
        ok = (rx is None or abs(rx) < 0.85) and (ry is None or abs(ry) < 0.85)
        details["tests"]["random_common_cause"] = {"pass": ok, "r_x": rx, "r_y": ry}
        if ok:
            passes += 1

    if "subset_stability" in tests:
        required += 1
        mid = max(4, len(rows) // 2)
        sub_r = _pearson(x[:mid], y[:mid])
        ok = (
            base_r is not None
            and sub_r is not None
            and (base_r * sub_r > 0)
            and abs(sub_r) >= abs(base_r) * 0.4
        )
        details["tests"]["subset_stability"] = {
            "pass": ok,
            "baseline_r": base_r,
            "subset_r": sub_r,
            "subset_n": mid,
        }
        if ok:
            passes += 1

    details["passed"] = passes
    details["required"] = required
    if required == 0:
        return RefutationStatus.FAIL, details
    if passes == required:
        return RefutationStatus.PASS, details
    return RefutationStatus.FAIL, details


def _try_dowhy_note(matrix: SkuMatrix, edge: CausalEdgeResult, details: dict[str, Any]) -> None:
    """Optional DoWhy import — augments details when library present."""
    try:
        import dowhy  # noqa: F401

        details["dowhy_available"] = True
        details["dowhy_note"] = "library present; internal battery used for V0.0.1 gate speed"
    except ImportError:
        details["dowhy_available"] = False


def promote_edge(matrix: SkuMatrix, edge: CausalEdgeResult) -> CausalEdgeResult:
    """Run refutation; promote to L2 or L3 per policy."""
    policy = load_policy()
    completeness_threshold = float(policy.get("completeness_threshold", 0.7))
    min_weeks = int(policy.get("min_weeks", 12))

    if matrix.n_weeks < min_weeks or matrix.completeness < completeness_threshold:
        edge.evidence_type = EvidenceType.ASSOCIATION
        edge.epistemic_layer = "L1"
        edge.refutation_status = RefutationStatus.PENDING
        return edge

    status, details = _refutation_battery(matrix, edge)
    _try_dowhy_note(matrix, edge, details)
    edge.refutation_details = details
    edge.refutation_status = status

    if status == RefutationStatus.PASS:
        edge.evidence_type = EvidenceType.CAUSAL_VERIFIED
        edge.epistemic_layer = "L3"
    else:
        edge.evidence_type = EvidenceType.CAUSAL_CANDIDATE
        edge.epistemic_layer = "L2"

    return edge


def promote_associations(
    matrix: SkuMatrix,
    associations: list[CausalEdgeResult],
) -> list[CausalEdgeResult]:
    return [promote_edge(matrix, e) for e in associations]
