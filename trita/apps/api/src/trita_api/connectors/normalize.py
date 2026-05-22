"""Map API/fixture records → RawEvent lists."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_dlt.envelope import RawEvent


def unicommerce_to_events(
    tenant_id: UUID, records: list[dict[str, Any]], *, account_ref: str, fixture: bool
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for row in records:
        sku = str(row.get("sku_code") or row.get("itemSku") or row.get("sku", ""))
        if not sku:
            continue
        events.append(
            RawEvent(
                tenant_id=tenant_id,
                source="unicommerce",
                external_id=f"{account_ref}:{sku}",
                entity_type="inventory",
                payload=row,
                lineage={"account_ref": account_ref, "fixture": fixture},
            )
        )
    return events


def shiprocket_to_events(
    tenant_id: UUID, records: list[dict[str, Any]], *, fixture: bool
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for row in records:
        ext = str(row.get("id") or row.get("order_id") or "")
        if not ext:
            continue
        events.append(
            RawEvent(
                tenant_id=tenant_id,
                source="shiprocket",
                external_id=ext,
                entity_type="shipment",
                payload=row,
                lineage={"fixture": fixture},
            )
        )
    return events


def razorpay_to_events(
    tenant_id: UUID, records: list[dict[str, Any]], *, fixture: bool
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for row in records:
        ext = str(row.get("id") or "")
        if not ext:
            continue
        events.append(
            RawEvent(
                tenant_id=tenant_id,
                source="razorpay",
                external_id=ext,
                entity_type="payout",
                payload=row,
                lineage={"fixture": fixture},
            )
        )
    return events


def normalize(
    source: str,
    tenant_id: UUID,
    records: list[dict[str, Any]],
    *,
    account_ref: str,
    fixture: bool,
) -> list[RawEvent]:
    if source == "unicommerce":
        return unicommerce_to_events(tenant_id, records, account_ref=account_ref, fixture=fixture)
    if source == "shiprocket":
        return shiprocket_to_events(tenant_id, records, fixture=fixture)
    if source == "razorpay":
        return razorpay_to_events(tenant_id, records, fixture=fixture)
    raise ValueError(f"Unknown source {source}")
