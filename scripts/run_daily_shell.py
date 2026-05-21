#!/usr/bin/env python3
"""Execute P-ORCH-DAILY-SHELL once (VA-09 / T-P0-051).

Usage (from repo root, after pip install -e trita/data/orchestration):
  python scripts/run_daily_shell.py

Or Dagster CLI (from trita/data/orchestration):
  dagster job execute -m trita_orchestration -j daily_shell_job
"""

from __future__ import annotations

import sys
from pathlib import Path

ORCH_SRC = Path(__file__).resolve().parents[1] / "trita" / "data" / "orchestration" / "src"
if str(ORCH_SRC) not in sys.path:
    sys.path.insert(0, str(ORCH_SRC))

from trita_orchestration.definitions import defs  # noqa: E402
from trita_orchestration.env import load_repo_env  # noqa: E402


def main() -> int:
    load_repo_env()
    job = defs.get_job_def("daily_shell_job")
    result = job.execute_in_process()
    if not result.success:
        print("daily_shell_job failed", file=sys.stderr)
        for event in result.all_events:
            if event.event_type_value == "STEP_FAILURE":
                print(event, file=sys.stderr)
        return 1
    print("daily_shell_job succeeded")
    for key, val in (result.output_for_node("integration_health_op") or {}).items():
        print(f"  {key}: {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
