"""LiteLLM proxy client — language only; no inventory math (VA-03)."""

from __future__ import annotations

import os
import re
from typing import Any
from uuid import UUID

import httpx

from trita_api.llm_budget import budget_exceeded, record_usage, tokens_used

FALLBACK_TEXT = (
    "Draft unavailable — tenant LLM budget reached. "
    "Use Data Health and gold metrics for inventory numbers."
)

SYSTEM_PROMPT = (
    "You write short merchant-facing copy for Trita. "
    "Never output reorder quantities, cover days, stock counts, or rupee impact. "
    "Refer the user to deterministic metrics in the product UI."
)

# VA-03 guard: reject model output that looks like computed inventory numbers
_INVENTORY_NUMBER_PATTERN = re.compile(
    r"(?i)(reorder|cover\s*days?|days?\s*cover|stockout|units?\s*to\s*order|"
    r"₹\s*[\d,]+|INR\s*[\d,]+|\b\d+\s*(units?|pcs|pieces)\b)"
)


def _proxy_base() -> str | None:
    raw = os.environ.get("LITELLM_PROXY_URL", "").strip()
    return raw.rstrip("/") if raw else None


def _master_key() -> str | None:
    return os.environ.get("LITELLM_MASTER_KEY", "").strip() or None


def _model_for_purpose(purpose: str) -> str:
    if purpose == "chat":
        return "groq-chat"
    return "gemini-cards"


def _fallback_response(tenant_id: UUID, reason: str) -> dict[str, Any]:
    return {
        "text": FALLBACK_TEXT,
        "source": "fallback",
        "reason": reason,
        "tokens_used": 0,
        "tenant_tokens_total": tokens_used(tenant_id),
    }


def _sanitize_or_fallback(text: str, tenant_id: UUID) -> dict[str, Any]:
    if _INVENTORY_NUMBER_PATTERN.search(text):
        return _fallback_response(tenant_id, "inventory_numbers_in_output")
    return {
        "text": text.strip(),
        "source": "litellm",
        "reason": None,
        "tokens_used": 0,
        "tenant_tokens_total": tokens_used(tenant_id),
    }


def complete_draft(*, tenant_id: UUID, prompt: str, purpose: str = "card_copy") -> dict[str, Any]:
    """Return narrative draft or budget/template fallback."""
    if budget_exceeded(tenant_id):
        return _fallback_response(tenant_id, "budget_exceeded")

    proxy = _proxy_base()
    if not proxy:
        return _fallback_response(tenant_id, "proxy_not_configured")

    key = _master_key()
    if not key:
        return _fallback_response(tenant_id, "master_key_missing")

    model = _model_for_purpose(purpose)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 256,
    }
    try:
        response = httpx.post(
            f"{proxy}/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=60.0,
        )
    except httpx.HTTPError:
        return _fallback_response(tenant_id, "proxy_error")

    if response.status_code != 200:
        return _fallback_response(tenant_id, f"proxy_status_{response.status_code}")

    body = response.json()
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return _fallback_response(tenant_id, "invalid_proxy_response")

    usage = body.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    record_usage(tenant_id, total_tokens)

    result = _sanitize_or_fallback(text, tenant_id)
    result["tokens_used"] = total_tokens
    result["tenant_tokens_total"] = tokens_used(tenant_id)
    return result
