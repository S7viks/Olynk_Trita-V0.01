"""Raw envelope: tenant_id, source, external_id, entity_type, payload, hash, lineage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RawEvent:
    tenant_id: UUID
    source: str
    external_id: str
    entity_type: str
    payload: dict[str, Any]
    lineage: dict[str, Any] = field(default_factory=dict)
    ingested_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def payload_hash(self) -> str:
        return payload_hash(self.payload)

    def as_row(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "source": self.source,
            "external_id": self.external_id,
            "entity_type": self.entity_type,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "ingested_at": self.ingested_at.isoformat(),
            "lineage": self.lineage or None,
        }


def shopify_order_event(
    *,
    tenant_id: UUID,
    order_id: str | int,
    payload: dict[str, Any],
    lineage: dict[str, Any] | None = None,
) -> RawEvent:
    return RawEvent(
        tenant_id=tenant_id,
        source="shopify",
        external_id=str(order_id),
        entity_type="order",
        payload=payload,
        lineage=lineage or {},
    )


def shopify_inventory_event(
    *,
    tenant_id: UUID,
    inventory_item_id: str | int,
    payload: dict[str, Any],
    lineage: dict[str, Any] | None = None,
) -> RawEvent:
    return RawEvent(
        tenant_id=tenant_id,
        source="shopify",
        external_id=str(inventory_item_id),
        entity_type="inventory",
        payload=payload,
        lineage=lineage or {},
    )
