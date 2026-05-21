"""Dagster jobs — P-ORCH-DAILY-SHELL."""

from __future__ import annotations

from dagster import job

from trita_orchestration.shell_ops import dbt_run_op, integration_health_op, shopify_sync_op


@job(name="daily_shell_job", description="P-ORCH-DAILY-SHELL: Shopify ingest → dbt → health")
def daily_shell_job() -> None:
    integration_health_op(dbt_run_op(shopify_sync_op()))
