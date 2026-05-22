"""Connector registry — honest modes and SLA (integrations.md)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorSpec:
    source: str
    display_name: str
    mode: str  # api | csv_hub
    raw_table: str
    freshness_sla_hours: int
    phase: int
    tier: str = "production"  # production | beta


CONNECTOR_SOURCES: dict[str, ConnectorSpec] = {
    "shopify": ConnectorSpec(
        source="shopify",
        display_name="Shopify",
        mode="api",
        raw_table="raw.shopify_events",
        freshness_sla_hours=24,
        phase=0,
    ),
    "unicommerce": ConnectorSpec(
        source="unicommerce",
        display_name="Unicommerce",
        mode="api",
        raw_table="raw.unicommerce_events",
        freshness_sla_hours=8,
        phase=1,
    ),
    "tally": ConnectorSpec(
        source="tally",
        display_name="Tally",
        mode="csv_hub",
        raw_table="raw.csv_hub_events",
        freshness_sla_hours=168,
        phase=1,
    ),
    "shiprocket": ConnectorSpec(
        source="shiprocket",
        display_name="Shiprocket",
        mode="api",
        raw_table="raw.shiprocket_events",
        freshness_sla_hours=12,
        phase=1,
    ),
    "razorpay": ConnectorSpec(
        source="razorpay",
        display_name="Razorpay",
        mode="api",
        raw_table="raw.razorpay_events",
        freshness_sla_hours=24,
        phase=1,
    ),
    "delhivery": ConnectorSpec(
        source="delhivery",
        display_name="Delhivery",
        mode="api",
        raw_table="raw.delhivery_events",
        freshness_sla_hours=24,
        phase=3,
        tier="beta",
    ),
    "meta_ads": ConnectorSpec(
        source="meta_ads",
        display_name="Meta Ads",
        mode="api",
        raw_table="raw.meta_ads_events",
        freshness_sla_hours=24,
        phase=3,
        tier="beta",
    ),
    "google_ads": ConnectorSpec(
        source="google_ads",
        display_name="Google Ads",
        mode="api",
        raw_table="raw.google_ads_events",
        freshness_sla_hours=24,
        phase=3,
        tier="beta",
    ),
}

RM1_API_SOURCES = ("unicommerce", "shiprocket", "razorpay")
RM3_API_SOURCES = ("delhivery", "meta_ads", "google_ads")
API_SYNC_SOURCES = RM1_API_SOURCES + RM3_API_SOURCES


def get_spec(source: str) -> ConnectorSpec:
    key = source.strip().lower()
    if key not in CONNECTOR_SOURCES:
        raise KeyError(f"Unknown connector source: {source}")
    return CONNECTOR_SOURCES[key]
