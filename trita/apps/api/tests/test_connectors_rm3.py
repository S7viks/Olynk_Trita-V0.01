"""RM-3 beta connectors F-CONN-007..009."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.connectors.normalize import delhivery_to_events, meta_ads_to_events
from trita_api.db import ConnectorCredential
from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


def test_delhivery_normalize_shipment_entity(tenant_a_id: UUID) -> None:
    events = delhivery_to_events(
        tenant_a_id,
        [{"awb": "DL-1", "order_id": "O1", "status": "Delivered"}],
        fixture=True,
    )
    assert len(events) == 1
    assert events[0].entity_type == "shipment"
    assert events[0].external_id == "DL-1"


def test_meta_ads_normalize_daily_spend(tenant_a_id: UUID) -> None:
    events = meta_ads_to_events(
        tenant_a_id,
        [{"date": "2026-05-01", "spend": 100.0, "campaign_id": "c1"}],
        fixture=True,
    )
    assert events[0].entity_type == "ad_spend_daily"
    assert events[0].external_id == "2026-05-01:c1"


@patch("trita_api.routes.sources.upsert_integration_health")
@patch("trita_api.routes.sources.upsert_connector_credential")
def test_connect_delhivery_beta(
    mock_upsert_cred: MagicMock,
    mock_health: MagicMock,
    tenant_a_id: UUID,
) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        "/v1/sources/delhivery/connect",
        headers={"Authorization": f"Bearer {token}"},
        json={"api_key": "beta-pilot", "account_ref": "yoga-bar"},
    )
    assert response.status_code == 200
    assert response.json()["connected"] is True


@patch("trita_api.routes.sources.upsert_integration_health")
@patch("trita_api.routes.sources.sync_source")
@patch("trita_api.routes.sources.get_connector_credential")
def test_sync_meta_ads_fixture(
    mock_cred: MagicMock,
    mock_sync: MagicMock,
    mock_health: MagicMock,
    tenant_a_id: UUID,
) -> None:
    mock_cred.return_value = ConnectorCredential(
        tenant_id=tenant_a_id,
        source="meta_ads",
        account_ref="yoga-bar",
        access_token="enc",
        scopes="ads",
    )
    mock_sync.return_value = {
        "events": 14,
        "inserted": 14,
        "account_ref": "yoga-bar",
        "ingest_mode": "fixture",
    }
    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        "/v1/sources/meta_ads/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["events"] >= 1


def test_integrations_health_lists_rm3_sources(tenant_a_id: UUID) -> None:
    token = mint_test_token(tenant_id=tenant_a_id)
    with patch("trita_api.routes.integrations.list_integration_health", return_value=[]):
        with patch("trita_api.routes.integrations.get_shopify_credential", return_value=None):
            with patch("trita_api.routes.integrations.get_connector_credential", return_value=None):
                response = client.get(
                    "/v1/integrations/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
    assert response.status_code == 200
    rows = {i["source"]: i for i in response.json()["integrations"]}
    assert set(rows) == {
        "shopify",
        "unicommerce",
        "tally",
        "shiprocket",
        "razorpay",
        "delhivery",
        "meta_ads",
        "google_ads",
    }
    assert rows["delhivery"]["tier"] == "beta"
    assert rows["meta_ads"]["tier"] == "beta"
    assert rows["google_ads"]["tier"] == "beta"
    assert rows["shopify"]["tier"] == "production"


def test_connect_rejects_rm3_typo() -> None:
    token = mint_test_token()
    response = client.post(
        "/v1/sources/meta-ad/connect",
        headers={"Authorization": f"Bearer {token}"},
        json={"api_key": "x"},
    )
    assert response.status_code == 404


@patch("trita_api.connectors.fetch._load_fixture")
def test_fetch_google_ads_with_api_key(mock_load: MagicMock, tenant_a_id: UUID) -> None:
    from trita_api.connectors.fetch import fetch_google_ads_daily

    mock_load.return_value = [{"date": "2026-05-01", "spend": 1}]
    cred = ConnectorCredential(
        tenant_id=tenant_a_id,
        source="google_ads",
        account_ref="yb",
        access_token="x",
        scopes="",
    )
    out = fetch_google_ads_daily(cred)
    assert len(out) == 1
    mock_load.assert_called_once_with("google_ads")
