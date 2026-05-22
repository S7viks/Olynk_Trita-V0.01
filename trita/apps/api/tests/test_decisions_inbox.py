"""F-DEC-005, F-INBOX-003 — audit and inbox actions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)

DECISION_ID = uuid4()


@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
@patch("trita_api.routes.decisions.psycopg.connect")
def test_reject_requires_reason_enum(
    mock_connect: MagicMock,
    _mock_db: MagicMock,
    tenant_a_id: UUID,
) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        f"/v1/decisions/{DECISION_ID}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason_enum": "not_a_valid_reason"},
    )
    assert response.status_code == 400


@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
@patch("trita_api.routes.decisions.psycopg.connect")
def test_approve_decision(
    mock_connect: MagicMock,
    _mock_db: MagicMock,
    tenant_a_id: UUID,
) -> None:
    with patch("trita_decisions.inbox.approve_decision") as mock_approve:
        mock_approve.return_value = {
            "decision_id": str(DECISION_ID),
            "status": "approved",
        }
        mock_connect.return_value.__enter__.return_value = MagicMock()

        token = mint_test_token(tenant_id=tenant_a_id)
        response = client.post(
            f"/v1/decisions/{DECISION_ID}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
@patch("trita_api.routes.decisions.psycopg.connect")
def test_reject_decision_with_enum(
    mock_connect: MagicMock,
    _mock_db: MagicMock,
    tenant_a_id: UUID,
) -> None:
    with patch("trita_decisions.inbox.reject_decision") as mock_reject:
        mock_reject.return_value = {
            "decision_id": str(DECISION_ID),
            "status": "rejected",
            "reason_enum": "wrong_qty",
        }
        mock_connect.return_value.__enter__.return_value = MagicMock()

        token = mint_test_token(tenant_id=tenant_a_id)
        response = client.post(
            f"/v1/decisions/{DECISION_ID}/reject",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason_enum": "wrong_qty"},
        )
    assert response.status_code == 200
    assert response.json()["reason_enum"] == "wrong_qty"


@patch("trita_api.routes.decisions.database_url", return_value="postgresql://test")
@patch("trita_api.routes.decisions.psycopg.connect")
def test_inbox_list_by_tab(
    mock_connect: MagicMock,
    _mock_db: MagicMock,
    tenant_a_id: UUID,
) -> None:
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        mock_cur
    )
    with patch("trita_decisions.inbox.list_inbox") as mock_list:
        mock_list.return_value = [
            {
                "id": str(DECISION_ID),
                "type": "INVENTORY_DEAD_STOCK",
                "sku_id": "sku-1",
                "sku_code": "YB-001",
                "event": "dead_stock",
                "status": "open",
                "inr_floor": 5000,
                "preview": "L0 · dead_stock",
                "created_at": "2026-05-21T00:00:00+00:00",
            }
        ]
        token = mint_test_token(tenant_id=tenant_a_id)
        response = client.get(
            "/v1/decisions?tab=open",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["count"] == 1
