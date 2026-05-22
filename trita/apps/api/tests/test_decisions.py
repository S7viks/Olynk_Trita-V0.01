"""F-DEC-001..004 — contract, suppression, integrity, emit API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)

TENANT = UUID("11111111-1111-1111-1111-111111111101")


def _metric_row(**overrides: object) -> tuple:
    base = (
        TENANT,
        datetime(2026, 5, 21).date(),
        "sku-key-1",
        "YB-001",
        10.0,
        2.0,
        1.5,
        5.0,
        14,
        100.0,
        1000.0,
        False,
        True,
        False,
        20.0,
        14.0,
    )
    return base


def test_build_card_contract() -> None:
    from trita_decisions.contract import DecisionType, build_card, validate_card

    tid = uuid4()
    card = build_card(
        decision_id=uuid4(),
        tenant_id=tid,
        decision_type=DecisionType.INVENTORY_REORDER,
        sku_id="sku-1",
        event="stockout_risk",
        impact={"inr_floor": 1000, "horizon_days": 14, "assumptions": []},
        recommendation={"action_template": "create_po_draft", "parameters": {"qty": 5}},
        inaction_model={"inr_at_risk_if_ignored": 1000, "days_to_stockout": 5},
        evidence_refs=["feat.sku_metrics_daily:2026-05-21:sku-1"],
        missing_data=[],
        epistemic_layer="L0",
        suppression=f"{tid}:INVENTORY_REORDER:sku-1:2026-W21",
        projection="abc123",
    )
    validate_card(card)
    assert card["execution"]["tier"] == 1


def test_impact_floor_conservative() -> None:
    from trita_decisions.contract import DecisionType, MetricSnapshot
    from trita_decisions.impact import compute_impact, inr_floor_value

    snap = MetricSnapshot(
        tenant_id=TENANT,
        metric_date="2026-05-21",
        canonical_sku_id="sku-1",
        sku_code="YB-001",
        on_hand=10,
        velocity_7d=2,
        velocity_30d=1.5,
        days_of_cover=5,
        aging_days=14,
        unit_cost=100,
        capital_at_risk=1000,
        cogs_missing=False,
        stockout_risk=True,
        dead_stock=False,
        reorder_qty=20,
        lead_time_days=14,
    )
    impact = compute_impact(DecisionType.INVENTORY_REORDER, snap)
    assert inr_floor_value(impact) == 2000.0


def test_suppression_dedup_key_stable() -> None:
    from trita_decisions.contract import DecisionType, suppression_key

    when = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
    k1 = suppression_key(TENANT, DecisionType.INVENTORY_REORDER, "sku-a", when)
    k2 = suppression_key(TENANT, DecisionType.INVENTORY_REORDER, "sku-a", when)
    k3 = suppression_key(TENANT, DecisionType.INVENTORY_DEAD_STOCK, "sku-a", when)
    assert k1 == k2
    assert k1 != k3


def test_integrity_suppresses_degraded() -> None:
    from trita_decisions.integrity import HealthSnapshot, integrity_suppresses

    suppressed, source = integrity_suppresses(
        [
            HealthSnapshot("shopify", "degraded", datetime.now(UTC), 24),
            HealthSnapshot("unicommerce", "disconnected", None, 8),
        ]
    )
    assert suppressed is True
    assert source == "shopify"


def test_build_candidates_stockout_and_dead() -> None:
    from trita_decisions.candidates import build_candidates
    from trita_decisions.contract import MetricSnapshot

    snap_stockout = MetricSnapshot(
        tenant_id=TENANT,
        metric_date="2026-05-21",
        canonical_sku_id="sku-a",
        sku_code="A",
        on_hand=1,
        velocity_7d=2,
        velocity_30d=1,
        days_of_cover=1,
        aging_days=10,
        unit_cost=50,
        capital_at_risk=50,
        cogs_missing=False,
        stockout_risk=True,
        dead_stock=False,
        reorder_qty=10,
        lead_time_days=14,
    )
    snap_dead = MetricSnapshot(
        tenant_id=TENANT,
        metric_date="2026-05-21",
        canonical_sku_id="sku-b",
        sku_code="B",
        on_hand=100,
        velocity_7d=0,
        velocity_30d=0,
        days_of_cover=None,
        aging_days=120,
        unit_cost=20,
        capital_at_risk=2000,
        cogs_missing=False,
        stockout_risk=False,
        dead_stock=True,
        reorder_qty=0,
        lead_time_days=14,
    )
    candidates = build_candidates([snap_stockout, snap_dead])
    types = {c.decision_type.value for c in candidates}
    assert "INVENTORY_REORDER" in types
    assert "INVENTORY_DEAD_STOCK" in types


@patch("trita_decisions.emitter.append_audit")
@patch("trita_decisions.emitter.insert_decision")
@patch("trita_decisions.emitter.suppression_key_exists", return_value=False)
@patch("trita_decisions.emitter.remaining_weekly_quota", return_value=7)
@patch("trita_decisions.emitter.build_candidates")
@patch("trita_decisions.emitter.load_latest_metrics")
@patch("trita_decisions.emitter.check_integrity_suppress", return_value=(False, None))
def test_emit_respects_weekly_cap(
    mock_integrity: MagicMock,
    mock_load: MagicMock,
    mock_build: MagicMock,
    mock_quota: MagicMock,
    mock_dedup: MagicMock,
    mock_insert: MagicMock,
    _mock_audit: MagicMock,
) -> None:
    from trita_decisions.candidates import EmitCandidate
    from trita_decisions.contract import DecisionType, MetricSnapshot

    snap = MetricSnapshot(
        tenant_id=TENANT,
        metric_date="2026-05-21",
        canonical_sku_id="sku-x",
        sku_code="X",
        on_hand=1,
        velocity_7d=0,
        velocity_30d=0,
        days_of_cover=None,
        aging_days=100,
        unit_cost=10,
        capital_at_risk=100,
        cogs_missing=False,
        stockout_risk=False,
        dead_stock=True,
        reorder_qty=0,
        lead_time_days=14,
    )
    from trita_decisions.candidates import _build_candidate

    candidates = [
        _build_candidate(snap, DecisionType.INVENTORY_DEAD_STOCK, "dead_stock")
        for _ in range(10)
    ]
    mock_load.return_value = [snap]
    mock_build.return_value = candidates
    mock_insert.return_value = True

    mock_conn = MagicMock()
    mock_quota.return_value = 2

    from trita_decisions.emitter import emit_decisions

    result = emit_decisions(mock_conn, TENANT)
    assert result["emitted"] == 2
    assert result["skipped_cap"] == 8
    assert mock_insert.call_count == 2


@patch("trita_decisions.emitter.emit_decisions")
@patch("trita_api.routes.decisions.psycopg.connect")
@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
def test_decisions_emit_api(
    _mock_db_url: MagicMock,
    mock_connect: MagicMock,
    mock_emit: MagicMock,
    tenant_a_id: UUID,
) -> None:
    mock_connect.return_value.__enter__.return_value = MagicMock()
    mock_emit.return_value = {
        "tenant_id": str(tenant_a_id),
        "emitted": 3,
        "skipped_dedup": 0,
        "skipped_cap": 4,
        "integrity_suppressed": False,
        "candidates_considered": 27,
    }
    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        "/v1/decisions/emit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["emitted"] == 3


@patch("trita_decisions.emitter.check_integrity_suppress", return_value=(True, "shopify"))
def test_emit_integrity_suppressed(mock_int: MagicMock) -> None:
    mock_conn = MagicMock()
    from trita_decisions.emitter import emit_decisions

    result = emit_decisions(mock_conn, TENANT)
    assert result["integrity_suppressed"] is True
    assert result["emitted"] == 0
