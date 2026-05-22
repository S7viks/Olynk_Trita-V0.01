"""Ops for P-ORCH-DAILY-SHELL: ingest → dbt → health check."""

from __future__ import annotations

import os
import subprocess
import sys
import time
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
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(RUN_DBT), "run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise Failure(description=f"dbt run failed (exit {proc.returncode}): {tail}")

    return {"exit_code": 0, "stdout_tail": (proc.stdout or "")[-500:], "dbt_seconds": elapsed}


@op
def decision_emit_op(metrics_dbt: dict[str, Any]) -> dict[str, Any]:
    """Emit inventory decisions after metrics (P-DECISION-EMIT, F-DEC-001..004)."""
    del metrics_dbt
    load_repo_env()
    tenant_id = pilot_tenant_id()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise Failure(description="DATABASE_URL not set")
    try:
        from trita_decisions.emitter import emit_decisions
    except ImportError as exc:
        raise Failure(description=f"trita-decisions not installed: {exc}") from exc

    with psycopg.connect(url, autocommit=True) as conn:
        result = emit_decisions(conn, tenant_id)
    if result.get("integrity_suppressed"):
        raise Failure(
            description=f"Integrity suppress active ({result.get('integrity_source')})"
        )
    return result


@op
def integration_health_op(decision_emit: dict[str, Any]) -> dict[str, int]:
    """Verify raw + gold + feat metrics for pilot tenant (VA-09 / VA-14)."""
    del decision_emit
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

    from datetime import UTC, datetime

    from trita_api.integration_health import upsert_integration_health

    upsert_integration_health(
        tenant_id=tenant_id,
        source="shopify",
        status="healthy",
        last_sync_at=datetime.now(UTC),
        detail={"raw_events": raw_count, "gold_dim_sku": dim_sku_count},
    )

    metrics_count = 0
    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*) FROM feat.sku_metrics_daily WHERE tenant_id = %s
                """,
                (str(tenant_id),),
            )
            metrics_count = int(cur.fetchone()[0])

    if metrics_count <= 0:
        raise Failure(
            description=f"feat.sku_metrics_daily count is 0 for tenant {tenant_id}"
        )

    return {
        "raw_events": raw_count,
        "gold_dim_sku": dim_sku_count,
        "feat_sku_metrics_daily": metrics_count,
    }


@op
def identity_refresh_op(dbt_run: dict[str, Any]) -> dict[str, Any]:
    """Refresh sku_alias + order_bridge after gold marts (F-ID-001/002)."""
    del dbt_run
    load_repo_env()
    tenant_id = pilot_tenant_id()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise Failure(description="DATABASE_URL not set")
    try:
        from trita_ontology.refresh import refresh_identity
    except ImportError as exc:
        raise Failure(description=f"trita-ontology not installed: {exc}") from exc

    with psycopg.connect(url, autocommit=True) as conn:
        result = refresh_identity(conn, tenant_id)
    return result


@op
def metrics_dbt_op(identity_refresh: dict[str, Any]) -> dict[str, Any]:
    """Build feat.sku_metrics_daily after identity refresh (P-METRICS-DAILY)."""
    del identity_refresh
    load_repo_env()
    if not RUN_DBT.is_file():
        raise Failure(description=f"run_dbt script missing: {RUN_DBT}")
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(RUN_DBT), "run", "--select", "sku_metrics_daily"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise Failure(description=f"dbt metrics run failed: {tail}")
    return {"exit_code": 0, "dbt_seconds": elapsed}
