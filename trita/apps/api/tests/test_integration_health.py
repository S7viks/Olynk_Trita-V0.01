"""VA-06 — integration health API (F-CONN-HEALTH)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.integration_health import IntegrationHealthRow
from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


def test_integrations_health_requires_auth() -> None:
    response = client.get("/v1/integrations/health")
    assert response.status_code == 401


def test_integrations_health_shopify_disconnected(tenant_a_id: UUID) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    with patch("trita_api.routes.integrations.list_integration_health", return_value=[]):
        with patch("trita_api.routes.integrations.get_shopify_credential", return_value=None):
            with patch("trita_api.routes.integrations.get_connector_credential", return_value=None):
                response = client.get(
                    "/v1/integrations/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == str(tenant_a_id)
    integrations = body["integrations"]
    assert len(integrations) == 8
    shopify = next(i for i in integrations if i["source"] == "shopify")
    assert shopify["source"] == "shopify"
    assert shopify["status"] == "disconnected"
    assert shopify["last_sync_at"] is None
    assert shopify["detail"]["connected"] is False


def test_integrations_health_shopify_healthy_row(tenant_a_id: UUID) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    synced = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    row = IntegrationHealthRow(
        source="shopify",
        status="healthy",
        last_sync_at=synced,
        freshness_sla_hours=24,
        detail={"events": 10},
        updated_at=synced,
    )
    with patch("trita_api.routes.integrations.list_integration_health", return_value=[row]):
        with patch("trita_api.routes.integrations.get_shopify_credential", return_value=None):
            with patch("trita_api.routes.integrations.get_connector_credential", return_value=None):
                response = client.get(
                    "/v1/integrations/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
    assert response.status_code == 200
    shopify = next(i for i in response.json()["integrations"] if i["source"] == "shopify")
    assert shopify["status"] == "healthy"
    assert shopify["last_sync_at"] is not None


def test_integrations_health_tenant_isolation(tenant_b_id: UUID) -> None:
    token_b = mint_test_token(tenant_id=tenant_b_id)
    row = IntegrationHealthRow(
        source="shopify",
        status="healthy",
        last_sync_at=None,
        freshness_sla_hours=24,
        detail=None,
        updated_at=datetime.now(UTC),
    )

    def _list(tenant_id):  # noqa: ANN001
        assert tenant_id == tenant_b_id
        return [row]

    with patch("trita_api.routes.integrations.list_integration_health", side_effect=_list):
        with patch("trita_api.routes.integrations.get_shopify_credential", return_value=None):
            with patch("trita_api.routes.integrations.get_connector_credential", return_value=None):
                response = client.get(
                    "/v1/integrations/health",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(tenant_b_id)
