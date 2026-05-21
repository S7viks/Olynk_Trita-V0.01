from uuid import uuid4

from trita_dlt.shopify.pipeline import load_shopify_fixture, normalize_shopify_records


def test_yoga_bar_fixture_normalizes_orders_and_inventory() -> None:
    data = load_shopify_fixture()
    tenant_id = uuid4()
    events = normalize_shopify_records(
        tenant_id=tenant_id,
        orders=data["orders"],
        inventory_levels=data["inventory_levels"],
        shop_domain=data["shop_domain"],
    )
    types = {e.entity_type for e in events}
    assert types == {"order", "inventory"}
    assert all(e.tenant_id == tenant_id for e in events)
    assert all(e.source == "shopify" for e in events)
