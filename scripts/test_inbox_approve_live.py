#!/usr/bin/env python3
"""Live approve one REORDER card → Tier-2 drafts (manual E2E step 13)."""

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


def load_env() -> tuple[UUID, str, str]:
    env_path = REPO / ".env"
    if not env_path.is_file():
        raise SystemExit("Missing .env")
    tenant_id = api = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_id = UUID(line.split("=", 1)[1].strip())
        if line.startswith("NEXT_PUBLIC_API_URL="):
            api = line.split("=", 1)[1].strip().rstrip("/")
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
    api = api or os.environ.get("RENDER_HEALTH_URL", "http://127.0.0.1:8000").rstrip("/")
    if not tenant_id:
        raise SystemExit("YOGA_BAR_TENANT_ID required")
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise SystemExit("JWT secret required")
    token = jwt.encode(
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
    return tenant_id, api, token


def main() -> int:
    _tenant, api, token = load_env()
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=api, timeout=60.0) as client:
        open_body = client.get("/v1/decisions?tab=open", headers=headers).json()
        reorder = next(
            (i for i in open_body.get("items") or [] if i.get("type") == "INVENTORY_REORDER"),
            None,
        )
        if not reorder:
            print("No open INVENTORY_REORDER card — pick any open card or emit first.")
            items = open_body.get("items") or []
            if not items:
                return 1
            reorder = items[0]
        did = reorder["id"]
        print(f"Approving {did} ({reorder.get('sku_code')}) …")
        res = client.post(f"/v1/decisions/{did}/approve", headers=headers)
        print(f"HTTP {res.status_code}")
        body = res.json()
        print(json.dumps(body, indent=2)[:2000])
        if res.status_code != 200:
            return 1
        detail = client.get(f"/v1/decisions/{did}", headers=headers).json()
        arts = detail.get("decision", {}).get("artifacts") or []
        print(f"artifacts={len(arts)} timeline_actions={[e['action'] for e in detail.get('decision', {}).get('timeline', [])]}")
        return 0 if body.get("status") == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
