"""F-CAUSAL-001..003 — association, refutation gate, card enrich (VA-18, VA-19)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from trita_causal.association import scan_associations
from trita_causal.dowhy_runner import promote_edge
from trita_causal.enrich import enrich_card_from_db
from trita_causal.labels import l1_label, l3_label, narrative_for_edge
from trita_causal.policy import is_blocked_edge
from trita_causal.types import (
    CausalEdgeResult,
    EvidenceType,
    RefutationStatus,
    SkuMatrix,
    WeekRow,
)

TENANT = UUID("11111111-1111-1111-1111-111111111101")


def _synthetic_matrix(*, n: int = 14, ad_velocity_corr: bool = True) -> SkuMatrix:
    rows: list[WeekRow] = []
    for i in range(n):
        ad = float(100 + i * 5)
        if ad_velocity_corr:
            vel = ad * 0.02 + (i % 3) * 0.1
        else:
            vel = float(i % 5)
        rows.append(
            WeekRow(
                iso_week=f"2026-W{i + 1:02d}",
                values={
                    "velocity_7d": vel,
                    "ad_spend": ad,
                    "rto_rate": 0.05,
                    "payout_delay_days": 2.0,
                    "sessions": 0.0,
                },
            )
        )
    return SkuMatrix(
        tenant_id=TENANT,
        sku_id="sku-causal-1",
        rows=tuple(rows),
        n_weeks=n,
        completeness=1.0,
    )


def test_blocked_edge_policy() -> None:
    assert is_blocked_edge("ad_spend", "unit_cost", 0) is True
    assert is_blocked_edge("ad_spend", "velocity_7d", 7) is False
    assert is_blocked_edge("ad_spend", "velocity_7d", 30) is True


def test_l1_label_never_claims_causation() -> None:
    edge = CausalEdgeResult(
        tenant_id=TENANT,
        sku_id="s1",
        cause_variable="ad_spend",
        effect_variable="velocity_7d",
        evidence_type=EvidenceType.ASSOCIATION,
        epistemic_layer="L1",
        lag_days=7,
        correlation=0.62,
        confidence=0.62,
        refutation_status=RefutationStatus.PENDING,
        n_weeks=14,
        completeness=1.0,
    )
    text = l1_label(edge)
    assert "Correlated with" in text
    assert "cause" not in text.lower().split("—")[0]


def test_va18_l3_requires_refutation_pass() -> None:
    edge = CausalEdgeResult(
        tenant_id=TENANT,
        sku_id="s1",
        cause_variable="ad_spend",
        effect_variable="velocity_7d",
        evidence_type=EvidenceType.CAUSAL_VERIFIED,
        epistemic_layer="L3",
        lag_days=7,
        correlation=0.7,
        confidence=0.7,
        refutation_status=RefutationStatus.PASS,
        refutation_details={"tests": {"placebo": {"pass": True}}},
        n_weeks=14,
        completeness=1.0,
    )
    assert "Tested driver" in l3_label(edge)

    bad = CausalEdgeResult(
        tenant_id=TENANT,
        sku_id="s1",
        cause_variable="ad_spend",
        effect_variable="velocity_7d",
        evidence_type=EvidenceType.CAUSAL_CANDIDATE,
        epistemic_layer="L3",
        lag_days=7,
        correlation=0.7,
        confidence=0.7,
        refutation_status=RefutationStatus.FAIL,
        refutation_details={},
        n_weeks=14,
        completeness=1.0,
    )
    with pytest.raises(ValueError, match="refutation"):
        l3_label(bad)


def test_association_scan_finds_signal() -> None:
    matrix = _synthetic_matrix(n=14, ad_velocity_corr=True)
    edges = scan_associations(matrix)
    assert edges
    assert all(e.epistemic_layer == "L1" for e in edges)
    top = edges[0]
    assert top.cause_variable == "ad_spend"
    assert top.effect_variable == "velocity_7d"


def test_promote_edge_documents_refutation() -> None:
    matrix = _synthetic_matrix(n=14, ad_velocity_corr=True)
    assoc = scan_associations(matrix)
    assert assoc
    promoted = promote_edge(matrix, assoc[0])
    assert promoted.refutation_details.get("tests")
    assert promoted.refutation_status in (RefutationStatus.PASS, RefutationStatus.FAIL)
    if promoted.epistemic_layer == "L3":
        assert promoted.refutation_status == RefutationStatus.PASS
        assert promoted.refutation_details


def test_enrich_card_adds_l2_or_l3_evidence_refs() -> None:
    edge_id = str(uuid4())
    card = {
        "reasoning": {
            "causal_chain": [],
            "evidence_refs": ["feat.sku_metrics_daily:2026-05-21:sku-1"],
            "missing_data": [],
            "epistemic_layer": "L0",
        }
    }

    class FakeCur:
        def fetchone(self):
            return (
                edge_id,
                "ad_spend",
                "velocity_7d",
                "causal_candidate",
                "L2",
                7,
                0.65,
                0.65,
                "fail",
                {"tests": {"placebo": {"pass": False}}},
                narrative_for_edge(
                    CausalEdgeResult(
                        tenant_id=TENANT,
                        sku_id="sku-1",
                        cause_variable="ad_spend",
                        effect_variable="velocity_7d",
                        evidence_type=EvidenceType.CAUSAL_CANDIDATE,
                        epistemic_layer="L2",
                        lag_days=7,
                        correlation=0.65,
                        confidence=0.65,
                        refutation_status=RefutationStatus.FAIL,
                        n_weeks=14,
                        completeness=1.0,
                    )
                ),
            )

        def execute(self, *_a, **_k):
            return None

    enriched = enrich_card_from_db(
        FakeCur(),
        tenant_id=TENANT,
        sku_id="sku-1",
        card=card,
    )
    reasoning = enriched["reasoning"]
    assert reasoning["epistemic_layer"] in ("L2", "L3")
    refs = reasoning["evidence_refs"]
    assert any(r.startswith("analytics.causal_edges:") for r in refs)
    assert reasoning["causal_chain"]


def test_causal_run_api_route(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from trita_api.main import app
    from tests.conftest import mint_test_token

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test")

    def _fake_pipeline(_conn, tenant_id):  # type: ignore[no-untyped-def]
        return {
            "tenant_id": str(tenant_id),
            "skus_processed": 1,
            "edges_written": 1,
            "l1": 0,
            "l2": 1,
            "l3": 0,
        }

    monkeypatch.setattr(
        "trita_causal.runner.run_causal_pipeline",
        _fake_pipeline,
    )

    client = TestClient(app)
    token = mint_test_token(tenant_id=TENANT)
    with patch("psycopg.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = object()
        resp = client.post("/v1/causal/run", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["edges_written"] == 1
