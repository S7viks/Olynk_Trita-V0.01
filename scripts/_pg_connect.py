"""Postgres connect helper for CLI scripts (Supabase pooler-safe)."""

from __future__ import annotations

from typing import Any

import psycopg


def connect(url: str, **kwargs: Any) -> psycopg.Connection:
    """Use prepare_threshold=None on Supabase pooler (pgbouncer transaction mode)."""
    if "pooler.supabase.com" in url:
        kwargs.setdefault("prepare_threshold", None)
    return psycopg.connect(url, **kwargs)
