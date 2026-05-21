"""F-PLAT-003 routes — VA-03 + VA-07 HTTP contract."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from trita_api.llm_budget import reset_usage_for_tests
from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


def test_draft_rejects_body_tenant_override() -> None:
    tenant_id = uuid4()
    other = uuid4()
    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/llm/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Hello", "tenant_id": str(other)},
    )
    assert response.status_code == 403


@patch("trita_api.routes.llm.complete_draft")
def test_draft_route_returns_fallback_shape(mock_complete: MagicMock) -> None:
    tenant_id = uuid4()
    mock_complete.return_value = {
        "text": "Draft unavailable",
        "source": "fallback",
        "reason": "budget_exceeded",
        "tokens_used": 0,
        "tenant_tokens_total": 5001,
    }
    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/llm/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Explain drivers without numbers"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fallback"
    assert body["tenant_id"] == str(tenant_id)


@patch("trita_api.llm_client.httpx.post")
def test_va03_inventory_numbers_in_model_output_blocked(mock_post: MagicMock) -> None:
    reset_usage_for_tests()
    tenant_id = uuid4()
    os.environ["LITELLM_PROXY_URL"] = "http://127.0.0.1:4000"
    os.environ["LITELLM_MASTER_KEY"] = "test-key"
    os.environ["LITELLM_TENANT_TOKEN_BUDGET"] = "5000"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Reorder 500 units immediately."}}],
        "usage": {"total_tokens": 10},
    }
    mock_post.return_value = mock_resp

    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/llm/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Draft card"},
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fallback"
    assert response.json()["reason"] == "inventory_numbers_in_output"
