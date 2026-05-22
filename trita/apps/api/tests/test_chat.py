"""F-CHAT-001/002 — scope refusal and grounded evidence."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from trita_api.chat.handler import handle_chat_message
from trita_api.chat.scope import is_out_of_scope
from trita_api.main import app
from tests.conftest import mint_test_token

TENANT = UUID("11111111-1111-1111-1111-111111111101")
client = TestClient(app)


def test_refuse_ad_strategy() -> None:
    assert is_out_of_scope("Write my ad strategy for Meta")


def test_chat_refuses_out_of_scope() -> None:
    cur = MagicMock()
    out = handle_chat_message(
        cur,
        tenant_id=TENANT,
        message="Write my Facebook ads marketing plan",
        use_llm=False,
    )
    assert out["refused"] is True
    assert out["refusal_code"] == "out_of_scope"


def test_chat_grounded_sku_has_evidence_refs() -> None:
    cur = MagicMock()

    def execute(sql, params=None):
        q = " ".join(sql.split())
        if "integration_health" in q:
            cur.fetchone.return_value = ("shopify", "healthy", None)
        elif "count(*)" in q and "sku_metrics_daily" in q:
            cur.fetchone.return_value = (2, 1, "2026-05-21")
        elif "sku_code ILIKE" in q:
            cur.fetchone.return_value = (
                "sku-id-1",
                "YB-001",
                10.0,
                2.0,
                5.0,
                True,
                False,
                False,
            )
        elif "public.decisions" in q and "sku_id" in q:
            cur.fetchone.return_value = (uuid4(), "INVENTORY_REORDER", "open", 1000.0)
        elif "causal_edges" in q:
            cur.fetchone.return_value = None
        return None

    cur.execute.side_effect = execute
    out = handle_chat_message(
        cur,
        tenant_id=TENANT,
        message="What is stockout risk for YB-001?",
        use_llm=False,
    )
    assert out["refused"] is False
    assert out["evidence_refs"]
    assert any("feat.sku_metrics_daily" in r for r in out["evidence_refs"])


def test_chat_api_rejects_tenant_override() -> None:
    other = uuid4()
    token = mint_test_token(tenant_id=TENANT)
    resp = client.post(
        "/v1/chat/message",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "inventory health", "tenant_id": str(other)},
    )
    assert resp.status_code == 403


def test_chat_api_message_route() -> None:
    from unittest.mock import patch

    token = mint_test_token(tenant_id=TENANT)
    fake = {
        "refused": False,
        "answer": "ok",
        "evidence_refs": ["feat.sku_metrics_daily:2026-05-21:summary"],
        "source": "template",
    }
    with patch("trita_api.routes.chat.database_url", return_value="postgresql://test/test"):
        with patch("trita_api.routes.chat.handle_chat_message", return_value=fake):
            with patch(
                "trita_decisions.integrity.check_integrity_suppress",
                return_value=(False, None),
            ):
                with patch("psycopg.connect") as mock_conn:
                    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = MagicMock()
                    resp = client.post(
                        "/v1/chat/message",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"message": "inventory overview"},
                    )
    assert resp.status_code == 200
    assert resp.json()["evidence_refs"]
