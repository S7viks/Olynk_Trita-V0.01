"""Shopify API sync → raw (T-P0-011, T-P0-013 idempotency via writer)."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from trita_api.db import ShopifyCredential
from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


@patch("trita_api.routes.shopify.upsert_integration_health")
@patch("trita_api.routes.shopify.sync_records_to_raw")
@patch("trita_api.routes.shopify.fetch_products")
@patch("trita_api.routes.shopify.fetch_inventory_levels")
@patch("trita_api.routes.shopify.fetch_orders")
@patch("trita_api.routes.shopify.get_shopify_credential")
def test_sync_pulls_and_writes_raw(
    mock_cred: MagicMock,
    mock_orders: MagicMock,
    mock_inventory: MagicMock,
    mock_products: MagicMock,
    mock_sync: MagicMock,
    mock_health: MagicMock,
) -> None:
    tenant_id = uuid4()
    mock_cred.return_value = ShopifyCredential(
        tenant_id=tenant_id,
        shop_domain="yoga-bar.myshopify.com",
        access_token="shpat_secret",
        scopes="read_orders",
    )
    mock_orders.return_value = [{"id": 1}]
    mock_inventory.return_value = [{"inventory_item_id": 9, "available": 1}]
    mock_products.return_value = [{"id": 100, "title": "Test product"}]
    mock_sync.return_value = {"events": 2, "inserted": 2, "skipped": 0}

    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/sources/shopify/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 2
    assert "shpat" not in response.text
    mock_sync.assert_called_once()


def test_sync_requires_connection() -> None:
    with patch("trita_api.routes.shopify.get_shopify_credential", return_value=None):
        token = mint_test_token()
        response = client.post(
            "/v1/sources/shopify/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404
