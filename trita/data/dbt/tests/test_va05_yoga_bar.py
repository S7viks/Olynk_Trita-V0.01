"""VA-05 integration: raw → staging → gold for Yoga Bar (requires DATABASE_URL)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import psycopg
import pytest

REPO = Path(__file__).resolve().parents[4]
DBT_DIR = Path(__file__).resolve().parents[1]
RUN_DBT = REPO / "scripts" / "run_dbt.py"


def _load_env() -> None:
    env_path = REPO / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


@pytest.fixture(scope="module")
def database_url() -> str:
    _load_env()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


@pytest.mark.skipif(
    os.environ.get("TRITA_RUN_VA05", "").lower() not in ("1", "true", "yes"),
    reason="Set TRITA_RUN_VA05=1 to run live VA-05 path",
)
def test_va05_shopify_raw_to_gold(database_url: str) -> None:
    _load_env()
    tenant_raw = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    if not tenant_raw:
        pytest.skip("YOGA_BAR_TENANT_ID not set in .env")
    tenant_id = UUID(tenant_raw)

    with psycopg.connect(database_url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from raw.shopify_events where tenant_id = %s",
                (str(tenant_id),),
            )
            raw_count = cur.fetchone()[0]
    if raw_count == 0:
        pytest.skip("No raw.shopify_events for Yoga Bar — run Shopify sync first")

    # Prefer Python 3.13 env where dbt-postgres is installed (Windows dev layout)
    runners = [sys.executable]
    py313 = Path(r"C:\Python313\python.exe")
    if py313.is_file() and str(py313) not in runners:
        runners.insert(0, str(py313))

    proc = None
    for exe in runners:
        proc = subprocess.run(
            [exe, str(RUN_DBT), "run"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 or "dbt CLI not found" not in proc.stderr:
            break
    assert proc is not None
    assert proc.returncode == 0, proc.stdout + proc.stderr

    with psycopg.connect(database_url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from gold.dim_sku where tenant_id = %s",
                (str(tenant_id),),
            )
            dim_count = cur.fetchone()[0]
            cur.execute(
                "select count(*) from gold.fact_inventory_daily where tenant_id = %s",
                (str(tenant_id),),
            )
            inv_count = cur.fetchone()[0]
            cur.execute(
                "select count(*) from staging.stg_shopify_product_variants where tenant_id = %s",
                (str(tenant_id),),
            )
            stg_count = cur.fetchone()[0]

    assert stg_count > 0, "staging should have Yoga Bar variant rows"
    assert dim_count > 0, "gold.dim_sku should be populated for VA-05"
    assert inv_count > 0, "gold.fact_inventory_daily should be populated for VA-05"
