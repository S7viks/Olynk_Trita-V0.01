"""VA-09 integration: full Dagster daily_shell_job (requires .env + Shopify connected)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
RUN_SHELL = REPO / "scripts" / "run_daily_shell.py"
ORCH_DIR = REPO / "trita" / "data" / "orchestration"


@pytest.mark.skipif(
    os.environ.get("TRITA_RUN_VA09", "").lower() not in ("1", "true", "yes"),
    reason="Set TRITA_RUN_VA09=1 for live Dagster shell job",
)
def test_va09_daily_shell_job_execute() -> None:
    env = os.environ.copy()
    env_path = REPO / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env.setdefault(key.strip(), value.strip())
    if not env.get("DATABASE_URL") or not env.get("YOGA_BAR_TENANT_ID"):
        pytest.skip("DATABASE_URL and YOGA_BAR_TENANT_ID required in .env")

    proc = subprocess.run(
        [sys.executable, str(RUN_SHELL)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-3000:] + proc.stdout[-3000:]
