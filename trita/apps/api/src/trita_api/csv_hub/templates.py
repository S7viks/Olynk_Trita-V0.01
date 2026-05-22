"""Known CSV templates (tpl_*) — header auto-detect."""

from __future__ import annotations

from dataclasses import dataclass


def _norm(header: str) -> str:
    return header.strip().lower().replace("_", " ")


@dataclass(frozen=True)
class CsvTemplate:
    template_id: str
    logical_source: str
    entity_type: str
    display_name: str
    header_map: dict[str, list[str]]
    required_canonical: tuple[str, ...]


TEMPLATES: dict[str, CsvTemplate] = {
    "tpl_tally_stock": CsvTemplate(
        template_id="tpl_tally_stock",
        logical_source="tally",
        entity_type="unit_cost",
        display_name="Tally stock / valuation",
        header_map={
            "sku": ["stock item name", "item name", "sku", "product", "stock item"],
            "unit_cost": ["rate", "cost", "unit cost", "valuation", "value"],
            "qty": ["closing balance", "qty", "quantity", "closing qty"],
            "as_of": ["as on", "date", "as of", "period"],
        },
        required_canonical=("sku", "unit_cost"),
    ),
    "tpl_tally_sales": CsvTemplate(
        template_id="tpl_tally_sales",
        logical_source="tally",
        entity_type="order_line",
        display_name="Tally sales voucher",
        header_map={
            "sku": ["item", "stock item name", "product", "sku"],
            "order_id": ["voucher no", "voucher number", "invoice no", "order id"],
            "qty": ["qty", "quantity", "billed qty"],
            "occurred_at": ["date", "voucher date", "invoice date"],
        },
        required_canonical=("sku", "order_id", "qty", "occurred_at"),
    ),
    "tpl_generic_orders": CsvTemplate(
        template_id="tpl_generic_orders",
        logical_source="generic",
        entity_type="order_line",
        display_name="Generic orders CSV",
        header_map={
            "sku": ["sku", "product sku", "item sku", "variant sku"],
            "order_id": ["order id", "order", "order number", "invoice"],
            "qty": ["qty", "quantity", "units"],
            "occurred_at": ["date", "order date", "created at", "occurred at"],
        },
        required_canonical=("sku", "order_id", "qty", "occurred_at"),
    ),
}


def list_templates() -> list[dict[str, object]]:
    return [
        {
            "template_id": t.template_id,
            "logical_source": t.logical_source,
            "entity_type": t.entity_type,
            "display_name": t.display_name,
            "required_fields": list(t.required_canonical),
            "header_hints": t.header_map,
        }
        for t in TEMPLATES.values()
    ]


def detect_template(headers: list[str]) -> CsvTemplate | None:
    normalized = {_norm(h) for h in headers if h.strip()}
    best: CsvTemplate | None = None
    best_score = 0
    for tpl in TEMPLATES.values():
        score = 0
        for aliases in tpl.header_map.values():
            if any(a in normalized for a in aliases):
                score += 1
        required_hits = sum(
            1
            for field in tpl.required_canonical
            if any(a in normalized for a in tpl.header_map.get(field, []))
        )
        if required_hits < len(tpl.required_canonical):
            continue
        if score > best_score:
            best_score = score
            best = tpl
    return best


def build_column_map_from_template(tpl: CsvTemplate, headers: list[str]) -> dict[str, str]:
    """Map canonical field -> actual CSV header."""
    normalized_to_original = {_norm(h): h for h in headers}
    out: dict[str, str] = {}
    for canonical, aliases in tpl.header_map.items():
        for alias in aliases:
            if alias in normalized_to_original:
                out[canonical] = normalized_to_original[alias]
                break
    return out
