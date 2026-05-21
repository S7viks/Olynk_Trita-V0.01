"""Ops for P-ORCH-DAILY-SHELL: ingest → dbt → health check."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

import psycopg
from dagster import Failure, op

from trita_orchestration.env import REPO_ROOT, RUN_DBT, load_repo_env, pilot_tenant_id
from trita_orchestration.sync import run_shopify_sync


@op
def shopify_sync_op() -> dict[str, Any]:
    """Shopify Admin API → raw.shopify_events (pilot tenant from env)."""
    load_repo_env()
    result = run_shopify_sync()
    if result.get("events", 0) <= 0:
        raise Failure(description="Shopify sync produced zero events")
    return result


@op
def dbt_run_op(shopify_sync: dict[str, Any]) -> dict[str, Any]:
    """Run dbt project (staging + gold)."""
    del shopify_sync
    load_repo_env()
    if not RUN_DBT.is_file():
        raise Failure(description=f"run_dbt script missing: {RUN_DBT}")
    proc = subprocess.run(
        [sys.executable, str(RUN_DBT), "run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise Failure(description=f"dbt run failed (exit {proc.returncode}): {tail}")
    return {"exit_code": 0, "stdout_tail": (proc.stdout or "")[-500:]}


@op
def integration_health_op(dbt_run: dict[str, Any]) -> dict[str, int]:
    """Verify raw + gold row counts for pilot tenant (VA-09 proof)."""
    del dbt_run
    load_repo_env()
    tenant_id = pilot_tenant_id()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise Failure(description="DATABASE_URL not set")

    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from raw.shopify_events where tenant_id = %s",
                (str(tenant_id),),
            )
            raw_count = int(cur.fetchone()[0])
            cur.execute(
                "select count(*) from gold.dim_sku where tenant_id = %s",
                (str(tenant_id),),
            )
            dim_sku_count = int(cur.fetchone()[0])

    if raw_count <= 0:
        raise Failure(description=f"raw.shopify_events count is 0 for tenant {tenant_id}")
    if dim_sku_count <= 0:
        raise Failure(description=f"gold.dim_sku count is 0 for tenant {tenant_id}")

    return {"raw_events": raw_count, "gold_dim_sku": dim_sku_count}
