"""F-METRICS API read paths."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


@patch("trita_api.routes.metrics.database_url", return_value="postgresql://test")
@patch("trita_api.routes.metrics.psycopg.connect")
def test_metrics_summary(
    mock_connect: MagicMock, _mock_db_url: MagicMock, tenant_a_id: UUID
) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [
        (27, 2, 1, 5, 125000.0, date(2026, 5, 21)),
        (27,),
    ]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.get(
        "/v1/metrics/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sku_count"] == 27
    assert body["aligned"] is True


@patch("trita_api.routes.metrics.database_url", return_value="postgresql://test")
@patch("trita_api.routes.metrics.psycopg.connect")
def test_metrics_sku_list(
    mock_connect: MagicMock, _mock_db_url: MagicMock, tenant_a_id: UUID
) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = [
        (
            "sku-key-1",
            "YB-001",
            10,
            1.5,
            1.2,
            6.7,
            14,
            45.5,
            455.0,
            False,
            True,
            False,
            5,
            None,
        )
    ]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.get(
        "/v1/metrics/sku?stockout_only=true&limit=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["stockout_risk"] is True
