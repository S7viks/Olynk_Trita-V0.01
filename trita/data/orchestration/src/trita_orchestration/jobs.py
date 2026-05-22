"""Dagster jobs — P-ORCH-DAILY-SHELL."""

from __future__ import annotations

from dagster import job

from trita_orchestration.shell_ops import (
    dbt_run_op,
    decision_emit_op,
    identity_refresh_op,
    integration_health_op,
    metrics_dbt_op,
    shopify_sync_op,
)


@job(
    name="daily_shell_job",
    description="P-ORCH-DAILY-SHELL: ingest → dbt → identity → metrics → decisions → health",
)
def daily_shell_job() -> None:
    integration_health_op(
        decision_emit_op(
            metrics_dbt_op(identity_refresh_op(dbt_run_op(shopify_sync_op())))
        )
    )
