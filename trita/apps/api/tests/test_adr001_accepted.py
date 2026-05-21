"""T-P0-050 / ADR-001: Dagster orchestrator decision is Accepted and wired in docs."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
ADR = REPO / "docs" / "adr" / "001-orchestrator.md"
ARCH_INDEX = REPO / "architecture" / "README.md"
PIPELINE_REGISTRY = REPO / "docs" / "pipelines" / "REGISTRY.md"
ORCH_SPEC = REPO / "docs" / "pipelines" / "P-ORCH-DAILY-SHELL.md"
ORCH_DIR = REPO / "trita" / "data" / "orchestration"


def test_adr001_file_status_accepted() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert re.search(r"^\*\*Status:\*\*\s*Accepted\s*$", text, re.MULTILINE), (
        "ADR-001 must have Status: Accepted"
    )
    assert "Dagster" in text
    assert "T-P0-050" in text


def test_architecture_index_lists_adr001_accepted() -> None:
    text = ARCH_INDEX.read_text(encoding="utf-8")
    assert "ADR-001" in text
    assert "Accepted" in text
    assert "001-orchestrator.md" in text


def test_pipeline_registry_orchestrator_dagster() -> None:
    text = PIPELINE_REGISTRY.read_text(encoding="utf-8")
    assert "ADR-001 Accepted" in text
    assert "P-ORCH-DAILY-SHELL" in text


def test_orch_daily_shell_spec_exists() -> None:
    assert ORCH_SPEC.is_file()
    assert "T-P0-051" in ORCH_SPEC.read_text(encoding="utf-8")


def test_orchestration_code_location_directory() -> None:
    assert ORCH_DIR.is_dir()
    assert (ORCH_DIR / "src" / "trita_orchestration" / "definitions.py").is_file()


def test_daily_shell_job_registered() -> None:
    defs_path = ORCH_DIR / "src" / "trita_orchestration" / "definitions.py"
    text = defs_path.read_text(encoding="utf-8")
    assert "daily_shell_job" in text
    assert "Definitions" in text
