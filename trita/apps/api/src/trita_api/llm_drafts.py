"""Schema-bound Tier-2 drafts via LiteLLM (F-DRAFT-001, F-DRAFT-002, VA-03)."""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from trita_decisions.draft_schemas import DraftSchemaError, validate_po_draft, validate_supplier_email

from trita_api.llm_client import complete_draft

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass
    match = _JSON_FENCE.search(text)
    if match:
        try:
            parsed = json.loads(match.group(1).strip())
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _po_prompt(card: dict[str, Any], template: dict[str, Any]) -> str:
    rec = card.get("recommendation") or {}
    params = rec.get("parameters") or {}
    sku = params.get("sku_code")
    qty = params.get("qty")
    return (
        "Return ONLY a JSON object (no markdown) for a purchase order draft.\n"
        f'Use exactly sku_code="{sku}" and qty={qty} in line_items[0] — do not change qty.\n'
        "Required keys: po_reference, supplier_name, supplier_email, currency (INR), "
        "line_items (array with sku_code, description, qty, uom), notes, requested_delivery_date.\n"
        f"Template to refine (keep qty): {json.dumps(template, separators=(',', ':'))}"
    )


def _email_prompt(card: dict[str, Any], bundle: dict[str, Any]) -> str:
    po = bundle.get("po_draft") or {}
    email = bundle.get("email") or {}
    sku = (card.get("recommendation") or {}).get("parameters", {}).get("sku_code")
    qty = (card.get("recommendation") or {}).get("parameters", {}).get("qty")
    return (
        "Return ONLY a JSON object for a supplier email draft.\n"
        f"Reference SKU {sku} and qty {qty} in prose but do not invent different quantities.\n"
        "Required keys: subject, body_text, to (array of emails), line_items_summary.\n"
        f"PO context: {json.dumps(po, separators=(',', ':'))}\n"
        f"Template: {json.dumps(email, separators=(',', ':'))}"
    )


def complete_tier2_po_draft(
    *,
    tenant_id: UUID,
    card: dict[str, Any],
    template: dict[str, Any],
) -> dict[str, Any] | None:
    rec = card.get("recommendation") or {}
    params = rec.get("parameters") or {}
    sku_code = str(params.get("sku_code") or "")
    try:
        expected_qty = int(params.get("qty") or 0)
    except (TypeError, ValueError):
        expected_qty = 0

    result = complete_draft(
        tenant_id=tenant_id,
        prompt=_po_prompt(card, template),
        purpose="tier2_po",
    )
    if result.get("source") != "litellm":
        return None

    parsed = _extract_json_object(str(result.get("text") or ""))
    if not parsed:
        return None
    try:
        validate_po_draft(parsed, expected_sku_code=sku_code, expected_qty=expected_qty)
    except DraftSchemaError:
        return None
    parsed["_source"] = "litellm"
    return parsed


def complete_tier2_supplier_email(
    *,
    tenant_id: UUID,
    card: dict[str, Any],
    bundle: dict[str, Any],
) -> dict[str, Any] | None:
    result = complete_draft(
        tenant_id=tenant_id,
        prompt=_email_prompt(card, bundle),
        purpose="tier2_email",
    )
    if result.get("source") != "litellm":
        return None

    parsed = _extract_json_object(str(result.get("text") or ""))
    if not parsed:
        return None
    try:
        validate_supplier_email(parsed)
    except DraftSchemaError:
        return None
    parsed["_source"] = "litellm"
    return parsed


def make_tier2_llm_fn(tenant_id: UUID):
    """Callable for trita_decisions.drafts.maybe_create_tier2_drafts."""

    def _fn(kind: str, card: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
        if kind == "po_draft":
            return complete_tier2_po_draft(
                tenant_id=tenant_id,
                card=card,
                template=context,
            )
        if kind == "supplier_email":
            return complete_tier2_supplier_email(
                tenant_id=tenant_id,
                card=card,
                bundle=context,
            )
        return None

    return _fn
