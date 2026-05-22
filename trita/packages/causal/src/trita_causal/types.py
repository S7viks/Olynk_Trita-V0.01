"""Causal edge types (F-CAUSAL-001..003)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class EvidenceType(str, Enum):
    ASSOCIATION = "association"
    CAUSAL_CANDIDATE = "causal_candidate"
    CAUSAL_VERIFIED = "causal_verified"


class RefutationStatus(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"


MATRIX_COLUMNS = (
    "velocity_7d",
    "ad_spend",
    "rto_rate",
    "payout_delay_days",
    "sessions",
)


@dataclass(frozen=True)
class WeekRow:
    iso_week: str
    values: dict[str, float]


@dataclass(frozen=True)
class SkuMatrix:
    tenant_id: UUID
    sku_id: str
    rows: tuple[WeekRow, ...]
    n_weeks: int
    completeness: float


@dataclass
class CausalEdgeResult:
    tenant_id: UUID
    sku_id: str
    cause_variable: str
    effect_variable: str
    evidence_type: EvidenceType
    epistemic_layer: str
    lag_days: int
    correlation: float | None
    confidence: float | None
    refutation_status: RefutationStatus
    refutation_details: dict[str, Any] = field(default_factory=dict)
    n_weeks: int = 0
    completeness: float = 0.0
    narrative: str = ""

    def evidence_ref(self, edge_id: str) -> str:
        return f"analytics.causal_edges:{edge_id}"

    def to_db_row(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "sku_id": self.sku_id,
            "cause_variable": self.cause_variable,
            "effect_variable": self.effect_variable,
            "evidence_type": self.evidence_type.value,
            "epistemic_layer": self.epistemic_layer,
            "lag_days": self.lag_days,
            "correlation": self.correlation,
            "confidence": self.confidence,
            "refutation_status": self.refutation_status.value,
            "refutation_details": self.refutation_details,
            "n_weeks": self.n_weeks,
            "completeness": self.completeness,
            "narrative": self.narrative,
        }


def layer_rank(layer: str) -> int:
    return {"L0": 0, "L1": 1, "L2": 2, "L3": 3}.get(layer, 0)
