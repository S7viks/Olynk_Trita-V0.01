"""CLI entry: load Shopify fixture or API payload into raw.shopify_events."""

from __future__ import annotations

import argparse
import os
from uuid import UUID

from trita_dlt.shopify.pipeline import load_shopify_fixture, normalize_shopify_records
from trita_dlt.writer import write_shopify_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Trita Shopify → raw ingest")
    parser.add_argument(
        "--tenant-id",
        required=True,
        help="Yoga Bar tenant UUID (from public.tenants)",
    )
    parser.add_argument(
        "--fixture",
        default="yoga_bar_sample.json",
        help="Fixture file under shopify/fixtures/",
    )
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)
    data = load_shopify_fixture(args.fixture)
    events = normalize_shopify_records(
        tenant_id=tenant_id,
        orders=data.get("orders"),
        inventory_levels=data.get("inventory_levels"),
        shop_domain=data.get("shop_domain", os.environ.get("SHOPIFY_SHOP_DOMAIN", "")),
    )
    inserted, skipped = write_shopify_events(events)
    print(f"shopify raw: inserted={inserted} skipped={skipped} total={len(events)}")


if __name__ == "__main__":
    main()
