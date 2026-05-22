#!/usr/bin/env python3
"""Run proactive triggers + optional weekly digest for Yoga Bar pilot."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "trita" / "packages" / "proactive" / "src"))
sys.path.insert(0, str(ROOT / "trita" / "packages" / "decisions" / "src"))

import psycopg  # noqa: E402

from trita_proactive.digest import send_weekly_digest  # noqa: E402
from trita_proactive.runner import run_proactive_triggers  # noqa: E402
from trita_decisions.integrity import check_integrity_suppress  # noqa: E402


def load_env() -> tuple[UUID, str]:
    tenant_raw = url = None
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        print("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required", file=sys.stderr)
        raise SystemExit(1)
    return UUID(tenant_raw), url


def main() -> int:
    tenant_id, url = load_env()
    with psycopg.connect(url, autocommit=True, connect_timeout=60) as conn:
        with conn.cursor() as cur:
            suppressed, source = check_integrity_suppress(cur, tenant_id)
        result = run_proactive_triggers(
            conn,
            tenant_id,
            integrity_suppressed=suppressed,
            integrity_source=source,
        )
        print("triggers:", result)
        with conn.cursor() as cur:
            digest = send_weekly_digest(cur, tenant_id)
        print("weekly_digest:", digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
