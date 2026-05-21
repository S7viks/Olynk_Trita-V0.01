"""Shopify → raw envelope normalizer (orders + inventory)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from trita_dlt.envelope import RawEvent, shopify_inventory_event, shopify_order_event

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def normalize_shopify_records(
    *,
    tenant_id: UUID,
    orders: list[dict[str, Any]] | None = None,
    inventory_levels: list[dict[str, Any]] | None = None,
    products: list[dict[str, Any]] | None = None,
    shop_domain: str = "unknown",
) -> list[RawEvent]:
    """Map Shopify API/webhook shapes into RawEvent list."""
    events: list[RawEvent] = []
    lineage_base = {"shop_domain": shop_domain, "api_version": "2024-10"}

    for order in orders or []:
        order_id = order.get("id") or order.get("order_id")
        if order_id is None:
            continue
        events.append(
            shopify_order_event(
                tenant_id=tenant_id,
                order_id=order_id,
                payload=order,
                lineage={**lineage_base, "resource": "orders"},
            )
        )

    for level in inventory_levels or []:
        ext_id = level.get("inventory_item_id") or level.get("id")
        if ext_id is None:
            continue
        events.append(
            shopify_inventory_event(
                tenant_id=tenant_id,
                inventory_item_id=ext_id,
                payload=level,
                lineage={**lineage_base, "resource": "inventory_levels"},
            )
        )

    for product in products or []:
        product_id = product.get("id")
        if product_id is None:
            continue
        events.append(
            shopify_inventory_event(
                tenant_id=tenant_id,
                inventory_item_id=product_id,
                payload=product,
                lineage={**lineage_base, "resource": "products"},
            )
        )

    return events


def load_shopify_fixture(name: str = "yoga_bar_sample.json") -> dict[str, Any]:
    path = FIXTURE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))
