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
}

RM1_API_SOURCES = ("unicommerce", "shiprocket", "razorpay")


def get_spec(source: str) -> ConnectorSpec:
    key = source.strip().lower()
    if key not in CONNECTOR_SOURCES:
        raise KeyError(f"Unknown connector source: {source}")
    return CONNECTOR_SOURCES[key]
