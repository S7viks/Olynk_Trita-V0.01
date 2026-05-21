"""T-P0-013 / VA-04 prep: duplicate (tenant, source, external_id, entity_type) is no-op."""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.skipif(
    os.environ.get("TRITA_RUN_ISOLATION") != "1",
    reason="Set TRITA_RUN_ISOLATION=1 and DATABASE_URL for Postgres idempotency test",
)

from trita_dlt.envelope import shopify_order_event
from trita_dlt.writer import write_shopify_events

TENANT_ID = UUID("11111111-1111-1111-1111-111111111101")


def test_duplicate_shopify_event_skipped(db_cleanup: None) -> None:
    event = shopify_order_event(
        tenant_id=TENANT_ID,
        order_id="idempotency-test-order",
        payload={"id": "idempotency-test-order", "probe": True},
        lineage={"shop_domain": "test.myshopify.com"},
    )
    first_inserted, first_skipped = write_shopify_events([event])
    second_inserted, second_skipped = write_shopify_events([event])
    assert first_inserted == 1
    assert first_skipped == 0
    assert second_inserted == 0
    assert second_skipped == 1


@pytest.fixture
def db_cleanup() -> None:
    yield
    url = os.environ["DATABASE_URL"]
    with psycopg.connect(url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM raw.shopify_events
                WHERE tenant_id = %s AND external_id = 'idempotency-test-order'
                """,
                (TENANT_ID,),
            )
