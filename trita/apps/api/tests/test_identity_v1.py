"""F-ID-001 / F-ID-002 identity v1."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from trita_api.main import app
from trita_ontology.bridge import build_order_bridge_rows
from trita_ontology.identity import build_line_variant_aliases, compute_resolution_stats
from trita_ontology.normalize import normalize_order_key
from tests.conftest import mint_test_token

client = TestClient(app)


def test_normalize_order_key_matches_shopify_and_channel() -> None:
    assert normalize_order_key("#YB-1001") == normalize_order_key("YB-SHOPIFY-1001")
    assert normalize_order_key("YB-SHOPIFY-1002") == "1002"


def test_build_order_bridge_join_rates() -> None:
    rows, stats = build_order_bridge_rows(
        [{"order_id": "1", "order_name": "#YB-1001"}],
        [{"shipment_id": "s1", "channel_order_id": "YB-SHOPIFY-1001"}],
        [{"payment_id": "p1", "channel_order_id": "YB-SHOPIFY-1001", "settlement_id": "set1"}],
    )
    assert stats.order_keys == 1
    assert stats.with_both == 1
    assert stats.full_bridge_rate == 1.0
    assert rows[0]["has_shipment"] and rows[0]["has_payment"]


def test_line_variant_aliases_resolve_all_lines() -> None:
    tenant_id = uuid4()
    lines = [{"variant_id": "101", "order_id": "1", "line_item_id": "a", "sku": "X"}]
    aliases = build_line_variant_aliases(tenant_id, lines, set())
    index = {(a["source"], a["external_id"]): a["canonical_sku_id"] for a in aliases}
    stats = compute_resolution_stats(lines, index)
    assert stats.resolution_rate == 1.0


@patch("trita_api.routes.identity.database_url", return_value="postgresql://test")
@patch("trita_ontology.refresh.refresh_identity")
def test_identity_refresh_endpoint(
    mock_refresh: MagicMock, _mock_db_url: MagicMock, tenant_a_id: UUID
) -> None:
    mock_refresh.return_value = {
        "resolution": {"resolution_rate": 0.95, "meets_va13": True},
        "bridge": {"full_bridge_rate": 1.0},
    }
    token = mint_test_token(tenant_id=tenant_a_id)
    with patch("trita_api.routes.identity.psycopg.connect") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        response = client.post(
            "/v1/identity/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["resolution"]["meets_va13"] is True


@patch("trita_api.routes.identity.database_url", return_value="postgresql://test")
@patch("trita_api.routes.identity.psycopg.connect")
def test_manual_alias_merge(
    mock_connect: MagicMock, _mock_db_url: MagicMock, tenant_a_id: UUID
) -> None:
    mock_cur = MagicMock()
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.post(
        "/v1/identity/aliases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source": "unicommerce",
            "external_id": "YB-PROTEIN-1KG",
            "canonical_sku_id": "abc123",
        },
    )
    assert response.status_code == 200
    assert response.json()["merged"] is True
