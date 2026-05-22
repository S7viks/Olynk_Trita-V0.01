"""RM-1 connectors F-CONN-002, 004, 006."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.db import ConnectorCredential
from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


@patch("trita_api.routes.sources.upsert_integration_health")
@patch("trita_api.routes.sources.upsert_connector_credential")
def test_connect_unicommerce_fixture_mode(
    mock_upsert_cred: MagicMock,
    mock_health: MagicMock,
    tenant_a_id: UUID,
) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    with patch.dict("os.environ", {"CONNECTOR_DEV_FIXTURES": "1"}, clear=False):
        response = client.post(
            "/v1/sources/unicommerce/connect",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_ref": "BOM-01"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    mock_upsert_cred.assert_called_once()


@patch("trita_api.routes.sources.upsert_integration_health")
@patch("trita_api.routes.sources.sync_source")
@patch("trita_api.routes.sources.get_connector_credential")
def test_sync_unicommerce_writes_events(
    mock_cred: MagicMock,
    mock_sync: MagicMock,
    mock_health: MagicMock,
    tenant_a_id: UUID,
) -> None:
    mock_cred.return_value = ConnectorCredential(
        tenant_id=tenant_a_id,
        source="unicommerce",
        account_ref="BOM-01",
        access_token="enc",
        scopes="api",
    )
    mock_sync.return_value = {
        "events": 2,
        "inserted": 2,
        "account_ref": "BOM-01",
        "ingest_mode": "fixture",
    }
    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        "/v1/sources/unicommerce/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["events"] >= 1


def test_integrations_health_lists_rm1_sources(tenant_a_id: UUID) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    with patch("trita_api.routes.integrations.list_integration_health", return_value=[]):
        with patch("trita_api.routes.integrations.get_shopify_credential", return_value=None):
            with patch("trita_api.routes.integrations.get_connector_credential", return_value=None):
                response = client.get(
                    "/v1/integrations/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
    assert response.status_code == 200
    sources = {i["source"] for i in response.json()["integrations"]}
    assert sources == {"shopify", "unicommerce", "tally", "shiprocket", "razorpay"}


def test_connect_rejects_unknown_source() -> None:
    token = mint_test_token()
    response = client.post(
        "/v1/sources/unknown/connect",
        headers={"Authorization": f"Bearer {token}"},
        json={"api_key": "x"},
    )
    assert response.status_code == 404
