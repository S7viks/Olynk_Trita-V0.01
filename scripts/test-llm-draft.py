#!/usr/bin/env python3
"""Smoke-test POST /v1/llm/draft (Yoga Bar JWT). API + optional LiteLLM must be running."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import jwt

REPO = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env_path = REPO / ".env"
    if not env_path.is_file():
        raise SystemExit("Missing .env — copy from .env.example")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def resolve_tenant_id() -> UUID:
    tid = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    if tid:
        return UUID(tid)
    raise SystemExit(
        "Set YOGA_BAR_TENANT_ID in .env (Supabase: select id from tenants where slug = 'yoga-bar')."
    )


def mint_jwt(tenant_id: UUID) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise SystemExit("SUPABASE_JWT_SECRET or API_JWT_SECRET required in .env")
    return jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "tenant_id": str(tenant_id),
            "role": "owner",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(hours=2),
        },
        secret,
        algorithm="HS256",
    )


def main() -> int:
    load_env()
    api_base = (
        os.environ.get("NEXT_PUBLIC_API_URL") or os.environ.get("RENDER_HEALTH_URL") or "http://127.0.0.1:8000"
    ).rstrip("/")
    litellm = os.environ.get("LITELLM_PROXY_URL", "").rstrip("/")

    print(f"API: {api_base}")
    if litellm:
        print(f"LiteLLM: {litellm}")
        try:
            r = httpx.get(f"{litellm}/health/liveliness", timeout=5.0)
            print(f"  LiteLLM health: {r.status_code}")
        except httpx.HTTPError as exc:
            print(f"  LiteLLM health: DOWN ({exc}) — draft will use template fallback")

    tenant_id = resolve_tenant_id()
    token = mint_jwt(tenant_id)
    payload = {
        "prompt": "Write two sentences about checking Data Health before acting on stock signals. No numbers.",
        "purpose": "card_copy",
    }
    try:
        response = httpx.post(
            f"{api_base}/v1/llm/draft",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=90.0,
        )
    except httpx.HTTPError as exc:
        print(f"FAIL — API not reachable: {exc}")
        print("Start Terminal 2: .\\scripts\\start-local.ps1")
        return 1

    print(f"HTTP {response.status_code}")
    try:
        body = response.json()
    except json.JSONDecodeError:
        print(response.text[:500])
        return 1

    print(json.dumps(body, indent=2)[:1200])
    if response.status_code != 200:
        return 1

    source = body.get("source")
    reason = body.get("reason")
    if source == "litellm":
        print("OK — live LiteLLM draft")
        return 0
    if source == "fallback":
        print(f"OK — fallback (VA-07): reason={reason}")
        if litellm and reason in ("proxy_error", "proxy_status_502", "proxy_status_503"):
            print("Hint: start LiteLLM — .\\scripts\\start-litellm.ps1")
        elif reason == "master_key_missing":
            print("Hint: set LITELLM_MASTER_KEY in .env (any random string)")
        elif reason == "proxy_not_configured":
            print("Hint: set LITELLM_PROXY_URL=http://127.0.0.1:4000 in .env")
        return 0
    print(f"Unexpected source: {source}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
