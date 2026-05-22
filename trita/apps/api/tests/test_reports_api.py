"""F-REPORT-HEALTH API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


@patch("trita_api.routes.reports.integrations_health")
@patch("trita_api.routes.reports.metrics_summary")
@patch("trita_api.routes.reports.identity_stats")
def test_data_health_report(
    mock_identity: MagicMock,
    mock_metrics: MagicMock,
    mock_integrations: MagicMock,
    tenant_a_id: UUID,
) -> None:
    mock_integrations.return_value = {
        "tenant_id": str(tenant_a_id),
        "integrations": [
            {"source": "shopify", "status": "healthy", "display_name": "Shopify"},
            {"source": "tally", "status": "degraded", "display_name": "Tally"},
        ],
    }
    mock_metrics.return_value = {
        "tenant_id": str(tenant_a_id),
        "sku_count": 27,
        "dim_sku_count": 27,
        "aligned": True,
        "stockout_risk_count": 0,
        "dead_stock_count": 1,
        "cogs_missing_count": 5,
        "capital_at_risk_total": 1000.0,
        "metric_date": "2026-05-21",
    }
    mock_identity.return_value = {
        "tenant_id": str(tenant_a_id),
        "alias_count": 10,
        "resolution": {
            "total_lines": 100,
            "resolved_lines": 95,
            "resolution_rate": 0.95,
            "meets_va13": True,
        },
        "bridge": {
            "order_keys": 5,
            "with_shipment": 3,
            "with_payment": 2,
            "with_both": 1,
            "full_bridge_rate": 0.2,
        },
    }

    token = mint_test_token(tenant_id=tenant_a_id)
    response = client.get(
        "/v1/reports/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["aligned"] is True
    assert body["summary"]["sku_mart_aligned"] is True
    assert body["summary"]["resolution_meets_va13"] is True
    statuses = [i["status"] for i in body["integrations"]]
    assert statuses[0] == "degraded"
    assert statuses[1] == "healthy"
