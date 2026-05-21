from uuid import uuid4

from trita_dlt.envelope import RawEvent, payload_hash, shopify_order_event


def test_payload_hash_stable() -> None:
    payload = {"id": 1, "sku": "A"}
    assert payload_hash(payload) == payload_hash({"sku": "A", "id": 1})


def test_raw_event_row_shape() -> None:
    tenant_id = uuid4()
    event = shopify_order_event(
        tenant_id=tenant_id,
        order_id="99",
        payload={"id": 99},
        lineage={"shop_domain": "test.myshopify.com"},
    )
    row = event.as_row()
    assert row["tenant_id"] == str(tenant_id)
    assert row["source"] == "shopify"
    assert row["external_id"] == "99"
    assert row["entity_type"] == "order"
    assert row["payload_hash"] == payload_hash({"id": 99})
    assert row["lineage"]["shop_domain"] == "test.myshopify.com"


def test_dedup_key_fields_present() -> None:
    event = RawEvent(
        tenant_id=uuid4(),
        source="shopify",
        external_id="1",
        entity_type="order",
        payload={"x": 1},
    )
    row = event.as_row()
    assert row["source"] == "shopify"
    assert row["external_id"] == "1"
    assert row["entity_type"] == "order"
