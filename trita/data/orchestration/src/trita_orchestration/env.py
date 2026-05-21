"""Load repo-root .env and resolve paths for subprocess / imports."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

ORCHESTRATION_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = ORCHESTRATION_DIR.parents[2]
API_SRC = REPO_ROOT / "trita" / "apps" / "api" / "src"
DLT_SRC = REPO_ROOT / "trita" / "data" / "dlt" / "src"
RUN_DBT = REPO_ROOT / "scripts" / "run_dbt.py"


def load_repo_env() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def ensure_api_import_paths() -> None:
    for path in (API_SRC, DLT_SRC):
        s = str(path)
        if path.is_dir() and s not in sys.path:
            sys.path.insert(0, s)


def pilot_tenant_id() -> UUID:
    load_repo_env()
    raw = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    if not raw:
        raise RuntimeError("YOGA_BAR_TENANT_ID is required in .env for P-ORCH-DAILY-SHELL")
    return UUID(raw)
