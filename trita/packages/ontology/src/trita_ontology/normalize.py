"""Normalization helpers for identity matching."""

from __future__ import annotations

import re


def norm_sku(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def normalize_order_key(value: str | None) -> str | None:
    """Map Shopify order name and channel_order_id to a shared bridge key."""
    if not value or not str(value).strip():
        return None
    s = str(value).strip().upper().lstrip("#")
    s = s.replace("YB-SHOPIFY-", "").replace("YB-", "").replace("SHOPIFY-", "")
    match = re.search(r"(\d+)\s*$", s)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)", s)
    return match.group(1) if match else s
