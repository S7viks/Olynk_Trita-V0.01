"""VA-07 — LiteLLM per-tenant budget returns fallback."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from trita_api.llm_budget import record_usage, reset_usage_for_tests, tenant_token_budget
from trita_api.llm_client import FALLBACK_TEXT, complete_draft


@pytest.fixture(autouse=True)
def _clear_budget() -> None:
    reset_usage_for_tests()
    yield
    reset_usage_for_tests()


def test_budget_exceeded_returns_fallback_without_proxy_call() -> None:
    tenant_id = uuid4()
    os.environ["LITELLM_TENANT_TOKEN_BUDGET"] = "10"
    record_usage(tenant_id, 11)

    with patch("trita_api.llm_client.httpx.post") as mock_post:
        result = complete_draft(tenant_id=tenant_id, prompt="Summarize stock risk in prose.")

    assert result["source"] == "fallback"
    assert result["reason"] == "budget_exceeded"
    assert FALLBACK_TEXT in result["text"]
    mock_post.assert_not_called()


def test_proxy_not_configured_returns_fallback() -> None:
    tenant_id = uuid4()
    os.environ.pop("LITELLM_PROXY_URL", None)
    result = complete_draft(tenant_id=tenant_id, prompt="Hello")
    assert result["source"] == "fallback"
    assert result["reason"] == "proxy_not_configured"


@patch("trita_api.llm_client.httpx.post")
def test_successful_completion_records_tokens(mock_post: MagicMock) -> None:
    tenant_id = uuid4()
    os.environ["LITELLM_PROXY_URL"] = "http://127.0.0.1:4000"
    os.environ["LITELLM_MASTER_KEY"] = "test-key"
    os.environ["LITELLM_TENANT_TOKEN_BUDGET"] = str(tenant_token_budget())

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Review your Data Health dashboard for trends."}}],
        "usage": {"total_tokens": 42},
    }
    mock_post.return_value = mock_resp

    result = complete_draft(tenant_id=tenant_id, prompt="Write a short note.")
    assert result["source"] == "litellm"
    assert result["tokens_used"] == 42
