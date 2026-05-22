"""F-PROACTIVE-001..004 — triggers, feed, digest caps."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

TENANT = UUID("11111111-1111-1111-1111-111111111101")
client = TestClient(app)


def test_feed_dedup_key_stable() -> None:
    from trita_proactive.feed import insert_feed_event

    cur = MagicMock()
    cur.fetchone.return_value = (uuid4(),)
    ok = insert_feed_event(
        cur,
        tenant_id=TENANT,
        trigger_id="TR-VEL-DELTA",
        severity="highlight",
        title="t",
        body="b",
        dedup_key="sku-1",
    )
    assert ok is True
    cur.execute.assert_called_once()


def test_weekly_digest_skips_second_send_same_day() -> None:
    from trita_proactive.digest import send_weekly_digest

    cur = MagicMock()
    cur.fetchone.return_value = (1,)
    first = send_weekly_digest(cur, TENANT)
    assert first.get("skipped") is True
    assert first.get("reason") == "weekly_already_sent_today"


def test_urgent_cap_one_per_day() -> None:
    from trita_proactive.digest import send_urgent_digest

    cur = MagicMock()
    cur.fetchone.side_effect = [(1,)]
    blocked = send_urgent_digest(cur, TENANT, title="x", message="y")
    assert blocked.get("skipped") is True


def test_proactive_feed_route() -> None:
    from unittest.mock import patch

    token = mint_test_token(tenant_id=TENANT)
    with patch("trita_api.routes.proactive.database_url", return_value="postgresql://test/test"):
        with patch("trita_proactive.feed.list_feed", return_value=[]):
            with patch("psycopg.connect") as mock_conn:
                mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = MagicMock()
                resp = client.get(
                    "/v1/proactive/feed",
                    headers={"Authorization": f"Bearer {token}"},
                )
    assert resp.status_code == 200
