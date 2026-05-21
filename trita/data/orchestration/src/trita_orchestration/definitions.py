"""Dagster Definitions — code location entrypoint."""

from __future__ import annotations

from dagster import Definitions

from trita_orchestration.jobs import daily_shell_job

defs = Definitions(jobs=[daily_shell_job])
