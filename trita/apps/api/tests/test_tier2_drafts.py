"""F-DRAFT-001, F-DRAFT-002 — Tier-2 drafts on approve (VA-03)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from trita_api.main import app
from trita_decisions.draft_schemas import DraftSchemaError, validate_po_draft
from trita_decisions.drafts import (
    build_template_po_draft,
    build_template_supplier_email,
    maybe_create_tier2_drafts,
    should_create_tier2_drafts,
)
from tests.conftest import mint_test_token

client = TestClient(app)

DECISION_ID = uuid4()


def _reorder_decision(qty: int = 12) -> dict:
    card = {
        "recommendation": {
            "action_template": "create_po_draft",
            "parameters": {"sku_code": "YB-TEST", "qty": qty},
        },
        "impact": {"horizon_days": 14},
    }
    return {
        "type": "INVENTORY_REORDER",
        "status": "open",
        "projection_hash": "abc123",
        "card": card,
    }


def test_should_create_tier2_for_reorder_only() -> None:
    assert should_create_tier2_drafts(_reorder_decision()) is True
    dead = _reorder_decision()
    dead["type"] = "INVENTORY_DEAD_STOCK"
    assert should_create_tier2_drafts(dead) is False


def test_validate_po_draft_qty_lock() -> None:
    po = build_template_po_draft(decision_id=uuid4(), card=_reorder_decision()["card"])
    validate_po_draft(po, expected_sku_code="YB-TEST", expected_qty=12)
    bad = {**po, "line_items": [{**po["line_items"][0], "qty": 99}]}
    try:
        validate_po_draft(bad, expected_sku_code="YB-TEST", expected_qty=12)
        raise AssertionError("expected DraftSchemaError")
    except DraftSchemaError:
        pass


def test_template_drafts_roundtrip() -> None:
    card = _reorder_decision()["card"]
    po = build_template_po_draft(decision_id=uuid4(), card=card)
    email = build_template_supplier_email(po_draft=po, card=card)
    validate_po_draft(po, expected_sku_code="YB-TEST", expected_qty=12)
    from trita_decisions.draft_schemas import validate_supplier_email

    validate_supplier_email(email)


def test_maybe_create_tier2_stores_artifacts() -> None:
    cur = MagicMock()
    cur.fetchone.side_effect = [
        (uuid4(),),
        (uuid4(),),
    ]
    decision = _reorder_decision()
    tenant_id = uuid4()
    user_id = uuid4()
    did = uuid4()

    with patch("trita_decisions.drafts.append_audit"):
        result = maybe_create_tier2_drafts(
            cur,
            tenant_id=tenant_id,
            decision_id=did,
            user_id=user_id,
            decision=decision,
            llm_fn=None,
        )

    assert result is not None
    assert result["po_draft"]["line_items"][0]["qty"] == 12
    assert "supplier_email" in result
    assert cur.execute.call_count >= 2


@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
@patch("trita_api.routes.decisions.psycopg.connect")
def test_approve_returns_tier2_when_created(
    mock_connect: MagicMock,
    _mock_db: MagicMock,
) -> None:
    tenant_id = uuid4()
    with patch("trita_decisions.inbox.approve_decision") as mock_approve:
        mock_approve.return_value = {
            "decision_id": str(DECISION_ID),
            "status": "approved",
            "tier2_drafts": {
                "sources": {"po_draft": "template", "supplier_email": "template"},
            },
        }
        mock_connect.return_value.__enter__.return_value = MagicMock()

        token = mint_test_token(tenant_id=tenant_id)
        response = client.post(
            f"/v1/decisions/{DECISION_ID}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert "tier2_drafts" in response.json()


@patch("trita_api.llm_drafts.complete_draft")
def test_tier2_po_rejects_llm_qty_change(mock_complete: MagicMock) -> None:
    from trita_api.llm_drafts import complete_tier2_po_draft

    mock_complete.return_value = {
        "source": "litellm",
        "text": '{"po_reference":"X","supplier_name":"S","supplier_email":"a@b.c",'
        '"currency":"INR","line_items":[{"sku_code":"YB-TEST","qty":999,"uom":"units"}],'
        '"notes":"n","requested_delivery_date":null}',
    }
    card = _reorder_decision()["card"]
    template = build_template_po_draft(decision_id=uuid4(), card=card)
    result = complete_tier2_po_draft(
        tenant_id=uuid4(),
        card=card,
        template=template,
    )
    assert result is None
