"""Contract tests for P-ORCH-DAILY-SHELL (no live Shopify/dbt)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
ORCH = REPO / "trita" / "data" / "orchestration"


def test_orchestration_package_layout() -> None:
    assert (ORCH / "pyproject.toml").is_file()
    assert (ORCH / "workspace.yaml").is_file()
    assert (ORCH / "src" / "trita_orchestration" / "definitions.py").is_file()


def test_definitions_exposes_daily_shell_job() -> None:
    pytest.importorskip("dagster")
    from trita_orchestration.definitions import defs

    assert "daily_shell_job" in defs.get_repository_def().job_names


def test_daily_shell_job_op_chain() -> None:
    pytest.importorskip("dagster")
    from trita_orchestration.definitions import defs

    job_def = defs.get_job_def("daily_shell_job")
    node_names = {n.name for n in job_def.nodes}
    assert "shopify_sync_op" in node_names
    assert "dbt_run_op" in node_names
    assert "identity_refresh_op" in node_names
    assert "metrics_dbt_op" in node_names
    assert "integration_health_op" in node_names
