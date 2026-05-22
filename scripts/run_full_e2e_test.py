#!/usr/bin/env python3
"""Full-stack E2E sanity: gates, pytest, live API smoke (Yoga Bar)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import jwt

REPO = Path(__file__).resolve().parents[1]
API_SRC = REPO / "trita" / "apps" / "api" / "src"
DECISIONS_SRC = REPO / "trita" / "packages" / "decisions" / "src"
DLT_ROOT = REPO / "trita" / "data" / "dlt"
DBT_ROOT = REPO / "trita" / "data" / "dbt"
ORCH_ROOT = REPO / "trita" / "data" / "orchestration"


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    steps: list[StepResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.steps.append(StepResult(name=name, ok=ok, detail=detail))

    def exit_code(self) -> int:
        return 0 if all(s.ok for s in self.steps) else 1


def load_env() -> None:
    env_path = REPO / ".env"
    if not env_path.is_file():
        raise SystemExit("Missing .env")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def run_cmd(name: str, cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> StepResult:
    merged = {**os.environ, **(env or {})}
    proc = subprocess.run(
        cmd,
        cwd=cwd or REPO,
        env=merged,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    summary = "\n".join(tail[-8:]) if tail else "(no output)"
    ok = proc.returncode == 0
    return StepResult(name=name, ok=ok, detail=f"exit={proc.returncode}\n{summary}")


def mint_jwt(tenant_id: UUID) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("API_JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT secret missing")
    return jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "tenant_id": str(tenant_id),
            "role": "owner",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(hours=2),
        },
        secret,
        algorithm="HS256",
    )


def live_api_smoke(report: Report) -> None:
    api_base = (
        os.environ.get("NEXT_PUBLIC_API_URL") or os.environ.get("RENDER_HEALTH_URL") or "http://127.0.0.1:8000"
    ).rstrip("/")
    tenant_raw = os.environ.get("YOGA_BAR_TENANT_ID", "").strip()
    if not tenant_raw:
        report.add("live_api", False, "YOGA_BAR_TENANT_ID unset")
        return

    tenant_id = UUID(tenant_raw)
    token = mint_jwt(tenant_id)
    headers = {"Authorization": f"Bearer {token}"}
    checks: list[tuple[str, str, int | None]] = []

    try:
        with httpx.Client(base_url=api_base, timeout=30.0) as client:
            r = client.get("/health")
            checks.append(("GET /health", "ok" if r.status_code == 200 else r.text[:120], r.status_code))

            for path in (
                "/v1/integrations/health",
                "/v1/metrics/summary",
                "/v1/metrics/sku?limit=5",
                "/v1/reports/health",
                "/v1/decisions?tab=open",
                "/v1/decisions?tab=done",
                "/v1/decisions/reject-reasons",
            ):
                r = client.get(path, headers=headers)
                checks.append((f"GET {path}", f"status={r.status_code}", r.status_code))

            open_body = client.get("/v1/decisions?tab=open", headers=headers).json()
            items = open_body.get("items") or []
            if items:
                did = items[0]["id"]
                r = client.get(f"/v1/decisions/{did}", headers=headers)
                checks.append((f"GET /v1/decisions/{did[:8]}…", f"status={r.status_code}", r.status_code))
                arts = client.get(f"/v1/decisions/{did}/artifacts", headers=headers)
                checks.append((f"GET artifacts", f"status={arts.status_code}", arts.status_code))

            done_body = client.get("/v1/decisions?tab=done", headers=headers).json()
            done_items = done_body.get("items") or []
            if done_items:
                did = done_items[0]["id"]
                r = client.get(f"/v1/decisions/{did}/timeline", headers=headers)
                checks.append((f"GET timeline", f"status={r.status_code}", r.status_code))

            r = client.post(
                "/v1/llm/draft",
                headers=headers,
                json={"prompt": "One sentence: check Data Health before acting.", "purpose": "card_copy"},
            )
            draft = r.json() if r.status_code == 200 else {}
            checks.append(
                (
                    "POST /v1/llm/draft",
                    f"status={r.status_code} source={draft.get('source')}",
                    r.status_code,
                )
            )

    except httpx.HTTPError as exc:
        report.add("live_api", False, f"API unreachable at {api_base}: {exc}")
        return

    failed = [c for c in checks if c[2] is None or c[2] >= 400]
    lines = [f"  {c[0]}: {c[1]}" for c in checks]
    report.add("live_api", len(failed) == 0, "\n".join(lines))


def main() -> int:
    load_env()
    report = Report()
    py = sys.executable
    path_extra = os.pathsep.join(
        str(p) for p in (API_SRC, DECISIONS_SRC) if p.exists()
    )
    os.environ["PYTHONPATH"] = path_extra + (
        os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else ""
    )

    print("=== Trita full E2E test run ===\n")

    gate_scripts: list[tuple[str, list[str]]] = [
        ("apply_migrations.py", []),
        ("verify_rm0_gate.py", ["--spine-only"]),
        ("verify_rm1_gate.py", []),
        ("verify_metrics_gate.py", []),
        ("verify_rm2_gate.py", []),
    ]
    for script, extra in gate_scripts:
        report.steps.append(
            run_cmd(f"script:{script}", [py, str(REPO / "scripts" / script), *extra])
        )

    report.steps.append(
        run_cmd(
            "pytest:api",
            [py, "-m", "pytest", "tests", "-q", "--tb=line"],
            cwd=REPO / "trita" / "apps" / "api",
        )
    )

    if (DLT_ROOT / "tests").exists():
        report.steps.append(
            run_cmd(
                "pytest:dlt",
                [py, "-m", "pytest", "tests", "-q", "--tb=line"],
                cwd=DLT_ROOT,
            )
        )

    if (DBT_ROOT / "tests").exists():
        report.steps.append(
            run_cmd(
                "pytest:dbt",
                [py, "-m", "pytest", "tests", "-q", "--tb=line"],
                cwd=DBT_ROOT,
            )
        )

    if (ORCH_ROOT / "tests").exists():
        report.steps.append(
            run_cmd(
                "pytest:orchestration",
                [py, "-m", "pytest", "tests", "-q", "--tb=line"],
                cwd=ORCH_ROOT,
            )
        )

    live_api_smoke(report)

    print("\n=== Results ===\n")
    for s in report.steps:
        mark = "PASS" if s.ok else "FAIL"
        print(f"[{mark}] {s.name}")
        if s.detail:
            for line in s.detail.splitlines()[:12]:
                print(f"       {line}")
        print()

    passed = sum(1 for s in report.steps if s.ok)
    print(f"Summary: {passed}/{len(report.steps)} passed")
    return report.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
