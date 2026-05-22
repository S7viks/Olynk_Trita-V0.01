"""Lagged association scan with FDR (F-CAUSAL-001)."""

from __future__ import annotations

import math
from typing import Any

from trita_causal.policy import is_blocked_edge, load_policy
from trita_causal.types import (
    CausalEdgeResult,
    EvidenceType,
    RefutationStatus,
    SkuMatrix,
    WeekRow,
)


def _series(rows: tuple[WeekRow, ...], key: str, lag: int = 0) -> list[float]:
    vals: list[float] = []
    for i, row in enumerate(rows):
        j = i - lag
        if j < 0:
            vals.append(float("nan"))
            continue
        vals.append(row.values.get(key, float("nan")))
    return vals


def _pearson(x: list[float], y: list[float]) -> float | None:
    pairs = [
        (a, b)
        for a, b in zip(x, y, strict=True)
        if not (math.isnan(a) or math.isnan(b))
    ]
    if len(pairs) < 4:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((a - mx) * (b - my) for a, b in pairs)
    den_x = math.sqrt(sum((a - mx) ** 2 for a in xs))
    den_y = math.sqrt(sum((b - my) ** 2 for b in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def benjamini_hochberg(p_values: list[float], alpha: float) -> list[bool]:
    """Return mask of discoveries (same order as p_values)."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda t: t[1])
    discoveries = [False] * m
    max_k = -1
    for rank, (idx, p) in enumerate(indexed, start=1):
        if p <= (rank / m) * alpha:
            max_k = rank
    if max_k < 0:
        return discoveries
    threshold = indexed[max_k - 1][1]
    for idx, p in indexed:
        if p <= threshold:
            discoveries[idx] = True
    return discoveries


def _p_from_r(r: float, n: int) -> float:
    if n < 4 or r is None:
        return 1.0
    t = abs(r) * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
    # Two-tailed normal approx for speed (n>=12 weeks typical)
    z = t
    tail = 1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return max(1e-6, min(1.0, 2 * tail))


def scan_associations(matrix: SkuMatrix) -> list[CausalEdgeResult]:
    """Pairwise lagged correlation with BH-FDR; emits L1 candidates."""
    policy = load_policy()
    alpha = float(policy.get("fdr_alpha", 0.05))
    max_lag = int(policy.get("max_lags_days", 14))
    min_weeks = int(policy.get("min_weeks", 12))

    if matrix.n_weeks < min_weeks:
        return []

    causes = ["ad_spend", "rto_rate", "payout_delay_days"]
    effects = ["velocity_7d", "rto_rate"]
    candidates: list[tuple[str, str, int, float, float]] = []

    for cause in causes:
        for effect in effects:
            if cause == effect:
                continue
            for lag in range(0, max_lag + 1):
                if is_blocked_edge(cause, effect, lag):
                    continue
                x = _series(matrix.rows, cause, lag=lag)
                y = _series(matrix.rows, effect, lag=0)
                r = _pearson(x, y)
                if r is None:
                    continue
                p = _p_from_r(r, len(matrix.rows))
                candidates.append((cause, effect, lag, r, p))

    if not candidates:
        return []

    mask = benjamini_hochberg([c[4] for c in candidates], alpha)
    out: list[CausalEdgeResult] = []
    for (cause, effect, lag, r, _p), keep in zip(candidates, mask, strict=True):
        if not keep:
            continue
        out.append(
            CausalEdgeResult(
                tenant_id=matrix.tenant_id,
                sku_id=matrix.sku_id,
                cause_variable=cause,
                effect_variable=effect,
                evidence_type=EvidenceType.ASSOCIATION,
                epistemic_layer="L1",
                lag_days=lag,
                correlation=round(r, 4),
                confidence=round(abs(r), 4),
                refutation_status=RefutationStatus.PENDING,
                n_weeks=matrix.n_weeks,
                completeness=matrix.completeness,
            )
        )
    out.sort(key=lambda e: abs(e.correlation or 0), reverse=True)
    top_k = int(policy.get("top_k_per_sku", 3))
    return out[:top_k]
