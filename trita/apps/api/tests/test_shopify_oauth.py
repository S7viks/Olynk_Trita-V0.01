"""Shopify OAuth — no webhooks; VA-04 deferred."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from trita_api.main import app
from trita_api.shopify_oauth import (
    authorize_url,
    build_oauth_state,
    normalize_shop_domain,
    verify_oauth_state,
)
from tests.conftest import mint_test_token

client = TestClient(app, follow_redirects=False)


def test_normalize_shop_domain() -> None:
    assert normalize_shop_domain("Yoga-Bar") == "yoga-bar.myshopify.com"
    assert normalize_shop_domain("shop.myshopify.com") == "shop.myshopify.com"


def test_oauth_state_roundtrip() -> None:
    tenant_id = uuid4()
    shop = "yoga-bar.myshopify.com"
    state = build_oauth_state(tenant_id=str(tenant_id), shop_domain=shop)
    parsed = verify_oauth_state(state)
    assert parsed["tenant_id"] == str(tenant_id)
    assert parsed["shop"] == shop


def test_connect_redirects_to_shopify() -> None:
    tenant_id = uuid4()
    token = mint_test_token(tenant_id=tenant_id)
    response = client.get(
        "/v1/sources/shopify/connect?shop=yoga-bar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "yoga-bar.myshopify.com/admin/oauth/authorize" in location
    assert "client_id=test-client-id" in location
    assert "redirect_uri=" in location
    assert "localhost%3A3000%2Fapi%2Fsources%2Fshopify%2Fcallback" in location


@patch("trita_api.routes.shopify.upsert_integration_health")
@patch("trita_api.routes.shopify.exchange_code")
@patch("trita_api.routes.shopify.upsert_shopify_credential")
def test_callback_stores_token_and_redirects(
    mock_upsert: MagicMock,
    mock_exchange: MagicMock,
    mock_health: MagicMock,
) -> None:
    tenant_id = uuid4()
    shop = "yoga-bar.myshopify.com"
    state = build_oauth_state(tenant_id=str(tenant_id), shop_domain=shop)
    mock_exchange.return_value = {"access_token": "shpat_test_token", "scope": "read_orders"}

    response = client.get(
        f"/v1/sources/shopify/callback?code=abc&shop={shop}&state={state}",
    )
    assert response.status_code == 302
    assert "/onboarding" in response.headers.get("location", "")
    assert "shopify=connected" in response.headers.get("location", "")
    mock_upsert.assert_called_once()
    args, kwargs = mock_upsert.call_args
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["shop_domain"] == shop
    assert "shpat" not in str(kwargs["access_token_encrypted"]) or kwargs[
        "access_token_encrypted"
    ] != "shpat_test_token"


def test_status_never_returns_access_token() -> None:
    with patch("trita_api.routes.shopify.get_shopify_credential", return_value=None):
        token = mint_test_token()
        response = client.get(
            "/v1/sources/shopify/status",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert "access_token" not in body
