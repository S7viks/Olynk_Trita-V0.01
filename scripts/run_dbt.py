#!/usr/bin/env python3
"""Run dbt against DATABASE_URL from repo .env (P-DBT-DAILY / VA-05)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
DBT_DIR = REPO / "trita" / "data" / "dbt"
PROFILES_DIR = DBT_DIR / "profiles"


def load_env() -> None:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


def apply_database_url(url: str) -> None:
    parsed = urlparse(url)
    os.environ["DBT_HOST"] = parsed.hostname or "127.0.0.1"
    os.environ["DBT_PORT"] = str(parsed.port or 5432)
    os.environ["DBT_USER"] = parsed.username or "postgres"
    os.environ["DBT_PASSWORD"] = parsed.password or ""
    os.environ["DBT_DATABASE"] = (parsed.path or "/postgres").lstrip("/")


def main() -> int:
    load_env()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in .env", file=sys.stderr)
        return 1
    apply_database_url(db_url)

    args = sys.argv[1:] or ["run"]
    dbt_bin = shutil.which("dbt")
    for scripts in (
        Path(sys.executable).parent / "Scripts",
        Path(os.environ.get("APPDATA", "")) / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "Scripts",
    ):
        candidate = scripts / "dbt.exe"
        if candidate.is_file():
            dbt_bin = str(candidate)
            break
    if not dbt_bin:
        print("dbt CLI not found — pip install dbt-postgres", file=sys.stderr)
        return 1
    cmd = [
        dbt_bin,
        *args,
        "--profiles-dir",
        str(PROFILES_DIR),
        "--project-dir",
        str(DBT_DIR),
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=DBT_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
