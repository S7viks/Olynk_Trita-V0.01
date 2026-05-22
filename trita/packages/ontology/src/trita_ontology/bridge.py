"""Order ↔ shipment ↔ payment bridge (F-ID-002)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trita_ontology.normalize import normalize_order_key


@dataclass(frozen=True)
class BridgeStats:
    order_keys: int
    with_shipment: int
    with_payment: int
    with_both: int
    shipment_rate: float
    payment_rate: float
    full_bridge_rate: float


def build_order_bridge_rows(
    shopify_orders: list[dict[str, Any]],
    shipments: list[dict[str, Any]],
    payouts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], BridgeStats]:
    keys: dict[str, dict[str, Any]] = {}

    for order in shopify_orders:
        key = normalize_order_key(order.get("order_name")) or normalize_order_key(
            str(order.get("order_id") or "")
        )
        if not key:
            continue
        keys.setdefault(
            key,
            {"channel_order_key": key, "has_shipment": False, "has_payment": False},
        )
        keys[key].update(
            {
                "channel_order_key": key,
                "shopify_order_id": str(order.get("order_id") or ""),
                "shopify_order_name": order.get("order_name"),
            }
        )

    for ship in shipments:
        key = normalize_order_key(ship.get("channel_order_id")) or normalize_order_key(
            ship.get("order_id")
        )
        if not key:
            continue
        keys.setdefault(
            key,
            {"channel_order_key": key, "has_shipment": False, "has_payment": False},
        )
        keys[key]["shipment_id"] = str(ship.get("shipment_id") or "")
        keys[key]["has_shipment"] = True

    for pay in payouts:
        key = normalize_order_key(pay.get("channel_order_id")) or normalize_order_key(
            pay.get("order_id")
        )
        if not key:
            continue
        keys.setdefault(
            key,
            {"channel_order_key": key, "has_shipment": False, "has_payment": False},
        )
        keys[key]["payment_id"] = str(pay.get("payment_id") or "")
        keys[key]["settlement_id"] = str(pay.get("settlement_id") or "")
        keys[key]["has_payment"] = True

    rows = list(keys.values())
    order_count = len(rows)
    with_ship = sum(1 for r in rows if r.get("has_shipment"))
    with_pay = sum(1 for r in rows if r.get("has_payment"))
    with_both = sum(1 for r in rows if r.get("has_shipment") and r.get("has_payment"))

    stats = BridgeStats(
        order_keys=order_count,
        with_shipment=with_ship,
        with_payment=with_pay,
        with_both=with_both,
        shipment_rate=(with_ship / order_count) if order_count else 0.0,
        payment_rate=(with_pay / order_count) if order_count else 0.0,
        full_bridge_rate=(with_both / order_count) if order_count else 0.0,
    )
    return rows, stats
