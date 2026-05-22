"""Decision card contract (F-DEC-001) — matches docs/context/decision-contract.md."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DecisionType(str, Enum):
    INVENTORY_REORDER = "INVENTORY_REORDER"
    INVENTORY_DEAD_STOCK = "INVENTORY_DEAD_STOCK"
    INVENTORY_CAPITAL_TRAP = "INVENTORY_CAPITAL_TRAP"
    INVENTORY_BLOCKED = "INVENTORY_BLOCKED"


REQUIRED_CARD_KEYS = frozenset(
    {
        "id",
        "tenant_id",
        "type",
        "sku_id",
        "event",
        "impact",
        "reasoning",
        "recommendation",
        "confidence",
        "inaction_model",
        "execution",
        "provenance_links",
        "suppression_key",
        "created_at",
    }
)


@dataclass(frozen=True)
class MetricSnapshot:
    tenant_id: UUID
    metric_date: str
    canonical_sku_id: str
    sku_code: str
    on_hand: float
    velocity_7d: float
    velocity_30d: float
    days_of_cover: float | None
    aging_days: int
    unit_cost: float | None
    capital_at_risk: float | None
    cogs_missing: bool
    stockout_risk: bool
    dead_stock: bool
    reorder_qty: float
    lead_time_days: float


def iso_week_key(when: datetime | None = None) -> str:
    dt = when or datetime.now(UTC)
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def suppression_key(tenant_id: UUID, decision_type: DecisionType, sku_id: str, when: datetime | None = None) -> str:
    return f"{tenant_id}:{decision_type.value}:{sku_id}:{iso_week_key(when)}"


def projection_hash(snapshot: MetricSnapshot) -> str:
    payload = {
        "tenant_id": str(snapshot.tenant_id),
        "metric_date": snapshot.metric_date,
        "canonical_sku_id": snapshot.canonical_sku_id,
        "on_hand": snapshot.on_hand,
        "velocity_7d": snapshot.velocity_7d,
        "days_of_cover": snapshot.days_of_cover,
        "stockout_risk": snapshot.stockout_risk,
        "dead_stock": snapshot.dead_stock,
        "capital_at_risk": snapshot.capital_at_risk,
        "cogs_missing": snapshot.cogs_missing,
        "reorder_qty": snapshot.reorder_qty,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def build_card(
    *,
    decision_id: UUID,
    tenant_id: UUID,
    decision_type: DecisionType,
    sku_id: str,
    event: str,
    impact: dict[str, Any],
    recommendation: dict[str, Any],
    inaction_model: dict[str, Any],
    evidence_refs: list[str],
    missing_data: list[str],
    epistemic_layer: str,
    suppression: str,
    projection: str,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    created = created_at or datetime.now(UTC)
    card = {
        "id": str(decision_id),
        "tenant_id": str(tenant_id),
        "type": decision_type.value,
        "sku_id": sku_id,
        "event": event,
        "impact": impact,
        "reasoning": {
            "causal_chain": [],
            "evidence_refs": evidence_refs,
            "missing_data": missing_data,
            "epistemic_layer": epistemic_layer,
        },
        "recommendation": recommendation,
        "confidence": {
            "completeness": 0.85 if not missing_data else 0.5,
            "staleness_hours": 0,
            "gated": bool(missing_data),
        },
        "inaction_model": inaction_model,
        "execution": {"tier": 1},
        "provenance_links": [],
        "suppression_key": suppression,
        "projection_hash": projection,
        "created_at": created.isoformat(),
    }
    validate_card(card)
    return card


def validate_card(card: dict[str, Any]) -> None:
    missing = REQUIRED_CARD_KEYS - set(card.keys())
    if missing:
        raise ValueError(f"card missing keys: {sorted(missing)}")
    if card["execution"].get("tier") != 1:
        raise ValueError("tier 3 external writes are disabled in V0.0.1")
