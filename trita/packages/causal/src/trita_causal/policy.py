"""Load causal policy.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_POLICY_PATH = Path(__file__).resolve().parent / "policy.yaml"


@lru_cache(maxsize=1)
def load_policy() -> dict[str, Any]:
    with _POLICY_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def is_blocked_edge(cause: str, effect: str, lag_days: int) -> bool:
    policy = load_policy()
    max_lag = int(policy.get("max_lag_days_blocked", 21))
    if lag_days > max_lag:
        return True
    for rule in policy.get("blocked_edges", []) or []:
        if rule.get("cause") == cause and rule.get("effect") == effect:
            return True
    return False
