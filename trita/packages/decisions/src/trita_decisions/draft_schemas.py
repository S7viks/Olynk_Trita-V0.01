"""Tier-2 draft JSON schemas (F-DRAFT-001, F-DRAFT-002)."""

from __future__ import annotations

from typing import Any


class DraftSchemaError(ValueError):
    pass


def _require_keys(obj: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise DraftSchemaError(f"{label} missing keys: {missing}")


def validate_po_draft(
    payload: dict[str, Any],
    *,
    expected_sku_code: str,
    expected_qty: int,
) -> None:
    """PO draft must include line items; qty must match deterministic engine."""
    _require_keys(
        payload,
        ("po_reference", "supplier_name", "line_items", "currency", "notes"),
        "po_draft",
    )
    if payload.get("currency") != "INR":
        raise DraftSchemaError("po_draft.currency must be INR")

    items = payload.get("line_items")
    if not isinstance(items, list) or not items:
        raise DraftSchemaError("po_draft.line_items must be a non-empty list")

    line = items[0]
    if not isinstance(line, dict):
        raise DraftSchemaError("po_draft.line_items[0] must be an object")

    sku = str(line.get("sku_code") or "")
    if sku != expected_sku_code:
        raise DraftSchemaError("po_draft line sku_code does not match decision")

    try:
        qty = int(line.get("qty"))
    except (TypeError, ValueError) as exc:
        raise DraftSchemaError("po_draft line qty must be an integer") from exc

    if qty != expected_qty:
        raise DraftSchemaError("po_draft qty must match recommendation.parameters.qty (VA-03)")


def validate_supplier_email(payload: dict[str, Any]) -> None:
    _require_keys(payload, ("subject", "body_text", "to"), "supplier_email")
    to_list = payload.get("to")
    if not isinstance(to_list, list) or not to_list:
        raise DraftSchemaError("supplier_email.to must be a non-empty list")
    if not all(isinstance(x, str) and x.strip() for x in to_list):
        raise DraftSchemaError("supplier_email.to entries must be non-empty strings")
