"""Refresh SKU aliases + order bridge for Yoga Bar pilot (F-ID-001, F-ID-002)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _pg_connect import connect as pg_connect
ONTOLOGY_SRC = REPO / "trita" / "packages" / "ontology" / "src"
if str(ONTOLOGY_SRC) not in sys.path:
    sys.path.insert(0, str(ONTOLOGY_SRC))


def load_env() -> None:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            import os

            os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip()


def main() -> int:
    load_env()
    from trita_ontology.refresh import refresh_identity

    tenant = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("YOGA_BAR_TENANT_ID="):
            from uuid import UUID

            tenant = UUID(line.split("=", 1)[1].strip())
            break
    if not tenant:
        print("YOGA_BAR_TENANT_ID missing in .env", file=sys.stderr)
        return 1

    url = __import__("os").environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1

    with pg_connect(url, autocommit=True) as conn:
        result = refresh_identity(conn, tenant)

    print(f"tenant_id={result['tenant_id']}")
    print(f"aliases_upserted={result['aliases_upserted']}")
    print(f"resolution_rate={result['resolution']['resolution_rate']}")
    print(f"meets_va13={result['resolution']['meets_va13']}")
    print(f"bridge_full_rate={result['bridge']['full_bridge_rate']}")
    return 0 if result["resolution"]["meets_va13"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
