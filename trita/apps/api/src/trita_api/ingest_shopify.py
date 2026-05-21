"""Write Shopify API payloads to raw.shopify_events via trita-dlt."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_dlt.shopify.pipeline import normalize_shopify_records
from trita_dlt.writer import write_shopify_events


def sync_records_to_raw(
    *,
    tenant_id: UUID,
    shop_domain: str,
    orders: list[dict[str, Any]],
    inventory_levels: list[dict[str, Any]],
    products: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    events = normalize_shopify_records(
        tenant_id=tenant_id,
        orders=orders,
        inventory_levels=inventory_levels,
        products=products,
        shop_domain=shop_domain,
    )
    inserted, skipped = write_shopify_events(events)
    return {
        "events": len(events),
        "inserted": inserted,
        "skipped": skipped,
    }
