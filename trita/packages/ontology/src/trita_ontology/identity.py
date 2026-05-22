"""SKU alias refresh and resolution stats (F-ID-001)."""

from __future__ import annotations

import hashlib

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from trita_ontology.normalize import norm_sku


def canonical_sku_key(tenant_id: UUID, variant_id: str) -> str:
    """Match gold.dim_sku sku_key (md5 tenant + variant)."""
    raw = f"{tenant_id}|{variant_id}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DimSkuRow:
    sku_key: str
    shopify_variant_id: str | None
    sku_code: str | None
    title: str | None


@dataclass(frozen=True)
class ResolutionStats:
    total_lines: int
    resolved_lines: int
    resolution_rate: float
    alias_count: int
    unresolved_sample: list[dict[str, Any]]


def build_shopify_aliases(rows: list[DimSkuRow]) -> list[dict[str, Any]]:
    aliases: list[dict[str, Any]] = []
    for row in rows:
        if not row.shopify_variant_id:
            continue
        aliases.append(
            {
                "source": "shopify",
                "external_id": row.shopify_variant_id,
                "canonical_sku_id": row.sku_key,
                "confidence": 1.0,
                "merged_by": "auto:dim_sku",
            }
        )
    return aliases


def build_line_variant_aliases(
    tenant_id: UUID,
    lines: list[dict[str, Any]],
    existing: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Ensure every order-line variant_id has a shopify alias."""
    aliases: list[dict[str, Any]] = []
    for line in lines:
        variant_id = str(line.get("variant_id") or "")
        if not variant_id:
            continue
        key = ("shopify", variant_id)
        if key in existing:
            continue
        aliases.append(
            {
                "source": "shopify",
                "external_id": variant_id,
                "canonical_sku_id": canonical_sku_key(tenant_id, variant_id),
                "confidence": 0.9,
                "merged_by": "auto:order_line",
            }
        )
        existing.add(key)
    return aliases


def match_external_to_dim(
    external_id: str,
    rows: list[DimSkuRow],
    *,
    source: str,
) -> tuple[str | None, float]:
    ext_norm = norm_sku(external_id)
    if not ext_norm:
        return None, 0.0
    for row in rows:
        if row.sku_code and norm_sku(row.sku_code) == ext_norm:
            return row.sku_key, 0.95
        if row.title and norm_sku(row.title) == ext_norm:
            return row.sku_key, 0.85
        if source == "tally" and row.title and ext_norm in norm_sku(row.title):
            return row.sku_key, 0.75
    return None, 0.0


def compute_resolution_stats(
    lines: list[dict[str, Any]],
    alias_index: dict[tuple[str, str], str],
    *,
    sample_limit: int = 20,
) -> ResolutionStats:
    resolved = 0
    unresolved: list[dict[str, Any]] = []
    for line in lines:
        variant_id = str(line.get("variant_id") or "")
        key = ("shopify", variant_id)
        if variant_id and key in alias_index:
            resolved += 1
        elif len(unresolved) < sample_limit:
            unresolved.append(
                {
                    "order_id": line.get("order_id"),
                    "line_item_id": line.get("line_item_id"),
                    "variant_id": variant_id,
                    "sku": line.get("sku"),
                }
            )
    total = len(lines)
    rate = (resolved / total) if total else 1.0
    return ResolutionStats(
        total_lines=total,
        resolved_lines=resolved,
        resolution_rate=rate,
        alias_count=len(alias_index),
        unresolved_sample=unresolved,
    )
