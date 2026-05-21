"""Per-tenant LiteLLM token budget (T-P0-031 / VA-07)."""

from __future__ import annotations

import os
from uuid import UUID

_usage: dict[str, int] = {}


def tenant_token_budget() -> int:
    return int(os.environ.get("LITELLM_TENANT_TOKEN_BUDGET", "5000"))


def tokens_used(tenant_id: UUID) -> int:
    return _usage.get(str(tenant_id), 0)


def record_usage(tenant_id: UUID, tokens: int) -> None:
    if tokens <= 0:
        return
    key = str(tenant_id)
    _usage[key] = _usage.get(key, 0) + tokens


def budget_exceeded(tenant_id: UUID, additional: int = 0) -> bool:
    return tokens_used(tenant_id) + additional > tenant_token_budget()


def reset_usage_for_tests() -> None:
    _usage.clear()
