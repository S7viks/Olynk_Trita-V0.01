"""Emit inventory decision cards for Yoga Bar pilot (F-DEC-001..004)."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import psycopg

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "trita" / "packages" / "decisions" / "src"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))


def load_env() -> UUID:
    tenant_raw = None
    url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        raise RuntimeError("YOGA_BAR_TENANT_ID and DATABASE_URL required")
    import os

    os.environ["DATABASE_URL"] = url
    return UUID(tenant_raw)


def main() -> int:
    tenant_id = load_env()
    from trita_decisions.emitter import emit_decisions

    url = __import__("os").environ["DATABASE_URL"]
    with psycopg.connect(url, autocommit=True) as conn:
        result = emit_decisions(conn, tenant_id)
    print(result)
    if result.get("integrity_suppressed"):
        print("WARN: integrity suppress active — no cards emitted", file=sys.stderr)
        return 2
    return 0 if result.get("emitted", 0) >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
