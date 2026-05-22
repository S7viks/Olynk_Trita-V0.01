"""Build emit candidates from feat.sku_metrics_daily (F-DEC-001)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from trita_decisions.contract import DecisionType, MetricSnapshot, build_card, projection_hash, suppression_key
from trita_decisions.impact import CAPITAL_TRAP_MIN_INR, compute_impact, inr_floor_value


@dataclass(frozen=True)
class EmitCandidate:
    decision_type: DecisionType
    sku_id: str
    event: str
    snapshot: MetricSnapshot
    card: dict[str, object]
    inr_floor: float
    suppression: str
    projection: str


def _snapshot_from_row(row: tuple) -> MetricSnapshot:
    return MetricSnapshot(
        tenant_id=row[0],
        metric_date=row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
        canonical_sku_id=str(row[2]),
        sku_code=str(row[3]),
        on_hand=float(row[4] or 0),
        velocity_7d=float(row[5] or 0),
        velocity_30d=float(row[6] or 0),
        days_of_cover=float(row[7]) if row[7] is not None else None,
        aging_days=int(row[8] or 0),
        unit_cost=float(row[9]) if row[9] is not None else None,
        capital_at_risk=float(row[10]) if row[10] is not None else None,
        cogs_missing=bool(row[11]),
        stockout_risk=bool(row[12]),
        dead_stock=bool(row[13]),
        reorder_qty=float(row[14] or 0),
        lead_time_days=float(row[15] or 14),
    )


def load_latest_metrics(cur, tenant_id: UUID) -> list[MetricSnapshot]:
    cur.execute(
        """
        SELECT
            m.tenant_id,
            m.metric_date,
            m.canonical_sku_id,
            m.sku_code,
            m.on_hand,
            m.velocity_7d,
            m.velocity_30d,
            m.days_of_cover,
            m.aging_days,
            m.unit_cost,
            m.capital_at_risk,
            m.cogs_missing,
            m.stockout_risk,
            m.dead_stock,
            m.reorder_qty,
            m.lead_time_days
        FROM feat.sku_metrics_daily AS m
        WHERE m.tenant_id = %s
          AND m.metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
        """,
        (tenant_id, tenant_id),
    )
    return [_snapshot_from_row(r) for r in cur.fetchall()]


def _build_candidate(
    snap: MetricSnapshot,
    decision_type: DecisionType,
    event: str,
    *,
    missing_data: list[str] | None = None,
    recommendation: dict[str, object] | None = None,
) -> EmitCandidate:
    impact = compute_impact(decision_type, snap)
    floor = inr_floor_value(impact)
    decision_id = uuid4()
    key = suppression_key(snap.tenant_id, decision_type, snap.canonical_sku_id)
    proj = projection_hash(snap)
    evidence = [f"feat.sku_metrics_daily:{snap.metric_date}:{snap.canonical_sku_id}"]

    if recommendation is None:
        if decision_type == DecisionType.INVENTORY_REORDER:
            recommendation = {
                "action_template": "create_po_draft",
                "parameters": {"qty": int(max(snap.reorder_qty, 0)), "sku_code": snap.sku_code},
            }
        elif decision_type == DecisionType.INVENTORY_DEAD_STOCK:
            recommendation = {
                "action_template": "review_dead_stock",
                "parameters": {"sku_code": snap.sku_code, "aging_days": snap.aging_days},
            }
        elif decision_type == DecisionType.INVENTORY_CAPITAL_TRAP:
            recommendation = {
                "action_template": "review_capital_trap",
                "parameters": {"sku_code": snap.sku_code},
            }
        else:
            recommendation = {
                "action_template": "resolve_blockers",
                "parameters": {"sku_code": snap.sku_code},
            }

    inaction = {
        "inr_at_risk_if_ignored": floor,
        "days_to_stockout": int(snap.days_of_cover) if snap.days_of_cover is not None else None,
    }

    card = build_card(
        decision_id=decision_id,
        tenant_id=snap.tenant_id,
        decision_type=decision_type,
        sku_id=snap.canonical_sku_id,
        event=event,
        impact=impact,
        recommendation=recommendation,
        inaction_model=inaction,
        evidence_refs=evidence,
        missing_data=missing_data or [],
        epistemic_layer="L0",
        suppression=key,
        projection=proj,
    )
    return EmitCandidate(
        decision_type=decision_type,
        sku_id=snap.canonical_sku_id,
        event=event,
        snapshot=snap,
        card=card,
        inr_floor=floor,
        suppression=key,
        projection=proj,
    )


def build_candidates(snapshots: list[MetricSnapshot]) -> list[EmitCandidate]:
    """Four card types per contract; priority sort by inr_floor desc."""
    out: list[EmitCandidate] = []

    for snap in snapshots:
        if snap.stockout_risk and not snap.cogs_missing:
            out.append(
                _build_candidate(snap, DecisionType.INVENTORY_REORDER, "stockout_risk")
            )
        elif snap.stockout_risk and snap.cogs_missing:
            out.append(
                _build_candidate(
                    snap,
                    DecisionType.INVENTORY_BLOCKED,
                    "stockout_risk_missing_cogs",
                    missing_data=["unit_cost"],
                )
            )

        if snap.dead_stock:
            if snap.cogs_missing:
                out.append(
                    _build_candidate(
                        snap,
                        DecisionType.INVENTORY_BLOCKED,
                        "dead_stock_missing_cogs",
                        missing_data=["unit_cost"],
                    )
                )
            else:
                out.append(
                    _build_candidate(snap, DecisionType.INVENTORY_DEAD_STOCK, "dead_stock")
                )

        capital = snap.capital_at_risk or 0.0
        if (
            not snap.dead_stock
            and not snap.stockout_risk
            and capital >= CAPITAL_TRAP_MIN_INR
            and snap.velocity_7d < (1.0 / 7.0)
        ):
            if snap.cogs_missing:
                continue
            out.append(
                _build_candidate(snap, DecisionType.INVENTORY_CAPITAL_TRAP, "capital_trap")
            )

    out.sort(key=lambda c: c.inr_floor, reverse=True)
    return out
