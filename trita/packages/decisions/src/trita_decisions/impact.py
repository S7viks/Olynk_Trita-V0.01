"""Conservative ₹ impact floors (F-DEC-004) — deterministic only."""

from __future__ import annotations

from trita_decisions.contract import DecisionType, MetricSnapshot

CAPITAL_TRAP_MIN_INR = 5_000.0
DEFAULT_HORIZON_DAYS = 14


def compute_impact(decision_type: DecisionType, snap: MetricSnapshot) -> dict[str, object]:
    """Return impact block with inr_floor (conservative, never LLM-derived)."""
    unit = snap.unit_cost or 0.0
    capital = snap.capital_at_risk or 0.0
    assumptions = [f"lead_time_days={int(snap.lead_time_days)}"]

    if decision_type == DecisionType.INVENTORY_REORDER:
        qty = max(float(snap.reorder_qty), 0.0)
        inr = qty * unit if unit > 0 else 0.0
        if inr == 0 and snap.days_of_cover is not None and snap.velocity_7d > 0:
            inr = snap.velocity_7d * unit * DEFAULT_HORIZON_DAYS
        return {
            "inr_floor": round(max(inr, 0.0), 2),
            "horizon_days": DEFAULT_HORIZON_DAYS,
            "assumptions": assumptions,
        }

    if decision_type == DecisionType.INVENTORY_DEAD_STOCK:
        return {
            "inr_floor": round(max(capital, 0.0), 2),
            "horizon_days": 90,
            "assumptions": ["dead_stock_rule=aging>90d_and_low_velocity"],
        }

    if decision_type == DecisionType.INVENTORY_CAPITAL_TRAP:
        return {
            "inr_floor": round(max(capital, 0.0), 2),
            "horizon_days": 30,
            "assumptions": ["capital_trap=slow_velocity_high_on_hand"],
        }

    return {
        "inr_floor": 0.0,
        "horizon_days": DEFAULT_HORIZON_DAYS,
        "assumptions": ["blocked=missing_prerequisites"],
    }


def inr_floor_value(impact: dict[str, object]) -> float:
    return float(impact.get("inr_floor") or 0.0)
