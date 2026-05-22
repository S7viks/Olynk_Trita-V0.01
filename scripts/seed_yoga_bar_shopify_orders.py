"""Ingest Yoga Bar Shopify order fixture into raw (VA-13 gate prep)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
DLT_SRC = REPO / "trita" / "data" / "dlt" / "src"
API_SRC = REPO / "trita" / "apps" / "api" / "src"
if str(DLT_SRC) not in sys.path:
    sys.path.insert(0, str(DLT_SRC))
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))


def load_env() -> tuple[UUID, str]:
    tenant_raw = None
    url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        raise RuntimeError("YOGA_BAR_TENANT_ID and DATABASE_URL required in .env")
    os.environ["DATABASE_URL"] = url
    return UUID(tenant_raw), url


def main() -> int:
    tenant_id, _url = load_env()
    from trita_dlt.shopify.pipeline import load_shopify_fixture, normalize_shopify_records
    from trita_dlt.writer import write_shopify_events

    data = load_shopify_fixture("yoga_bar_sample.json")
    orders = data.get("orders") or []
    if not orders:
        print("FAIL: fixture has no orders", file=sys.stderr)
        return 1

    events = normalize_shopify_records(
        tenant_id=tenant_id,
        orders=orders,
        inventory_levels=[],
        shop_domain=data.get("shop_domain", "yoga-bar.myshopify.com"),
    )
    inserted, skipped = write_shopify_events(events)
    print(f"tenant_id={tenant_id}")
    print(f"order_events={len(events)} inserted={inserted} skipped={skipped}")
    print("Next: python scripts/run_dbt.py run")
    print("      python scripts/refresh_identity.py")
    return 0 if inserted + skipped > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
