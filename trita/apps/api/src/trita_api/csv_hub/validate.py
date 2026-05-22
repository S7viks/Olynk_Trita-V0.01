"""Canonical row validation for CSV hub."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


REQUIRED_BY_ENTITY: dict[str, tuple[str, ...]] = {
    "order_line": ("sku", "order_id", "qty", "occurred_at"),
    "inventory_snapshot": ("sku", "qty", "as_of"),
    "unit_cost": ("sku", "unit_cost", "as_of"),
    "shipment": ("status",),
    "payout": ("reference_id", "amount", "settled_at"),
}


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def validate_canonical_row(
    entity_type: str,
    row: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    required = REQUIRED_BY_ENTITY.get(entity_type)
    if not required:
        return None, f"unknown_entity_type:{entity_type}"

    canonical: dict[str, Any] = {}
    for field in required:
        val = row.get(field)
        if val is None or str(val).strip() == "":
            if field == "as_of" and entity_type in ("unit_cost", "inventory_snapshot"):
                canonical["as_of"] = date.today().isoformat()
                continue
            return None, f"missing_{field}"

    if entity_type == "shipment":
        awb = str(row.get("awb") or row.get("sku") or "").strip()
        if not awb:
            return None, "missing_awb"
        canonical["awb"] = awb
        canonical["status"] = str(row["status"]).strip()
        shipped = _parse_date(row.get("shipped_at")) or _parse_date(row.get("occurred_at"))
        if not shipped:
            return None, "invalid_shipped_at"
        canonical["shipped_at"] = shipped
        return canonical, None

    if entity_type == "payout":
        for k, v in row.items():
            if v is not None and str(v).strip():
                canonical[k] = v
        return canonical, None

    canonical["sku"] = str(row["sku"]).strip()
    if entity_type == "order_line":
        canonical["order_id"] = str(row["order_id"]).strip()
        qty = _parse_decimal(row["qty"])
        if qty is None:
            return None, "invalid_qty"
        canonical["qty"] = float(qty)
        occurred = _parse_date(row["occurred_at"])
        if not occurred:
            return None, "invalid_occurred_at"
        canonical["occurred_at"] = occurred
    elif entity_type == "unit_cost":
        cost = _parse_decimal(row["unit_cost"])
        if cost is None:
            return None, "invalid_unit_cost"
        canonical["unit_cost"] = float(cost)
        as_of = _parse_date(row.get("as_of")) or date.today().isoformat()
        canonical["as_of"] = as_of
        if row.get("qty") is not None and str(row.get("qty")).strip():
            qty = _parse_decimal(row["qty"])
            if qty is not None:
                canonical["qty"] = float(qty)
    elif entity_type == "inventory_snapshot":
        qty = _parse_decimal(row["qty"])
        if qty is None:
            return None, "invalid_qty"
        canonical["qty"] = float(qty)
        as_of = _parse_date(row.get("as_of")) or date.today().isoformat()
        canonical["as_of"] = as_of
    return canonical, None
