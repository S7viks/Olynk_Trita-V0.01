"""Minimal Supabase REST client using .env (canonical project)."""

from __future__ import annotations

import os
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def rest_headers() -> dict[str, str]:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
        "NEXT_PUBLIC_SUPABASE_ANON_KEY", ""
    )
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def base_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/") + "/rest/v1"


def get_tenant_by_slug(slug: str) -> dict | None:
    load_env()
    url = f"{base_url()}/tenants"
    params = {"slug": f"eq.{slug}", "select": "id,slug,display_name"}
    r = httpx.get(url, headers=rest_headers(), params=params, timeout=30.0)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None
