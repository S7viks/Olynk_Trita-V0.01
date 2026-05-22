"""RM-2 gate: Yoga Bar has ≥1 decision with approve/reject audit (MISSION #25)."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import psycopg

REPO = Path(__file__).resolve().parents[1]


def load_env() -> tuple[UUID, str]:
    tenant_raw = url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        print("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required", file=sys.stderr)
        raise SystemExit(1)
    return UUID(tenant_raw), url


def main() -> int:
    tenant_id, url = load_env()
    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM public.decisions WHERE tenant_id = %s",
                (tenant_id,),
            )
            total = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT count(*) FROM public.decision_audit
                WHERE tenant_id = %s
                  AND action IN (
                      'approved'::public.decision_audit_action,
                      'rejected'::public.decision_audit_action
                  )
                """,
                (tenant_id,),
            )
            acted = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT count(*) FROM public.decision_audit
                WHERE tenant_id = %s AND action = 'emitted'::public.decision_audit_action
                """,
                (tenant_id,),
            )
            emitted_audit = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT count(*) FROM public.decision_audit
                WHERE tenant_id = %s
                  AND action = 'rejected'::public.decision_audit_action
                  AND reason_enum IS NULL
                """,
                (tenant_id,),
            )
            reject_missing_enum = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT action::text, reason_enum::text, created_at
                FROM public.decision_audit
                WHERE tenant_id = %s
                  AND action IN (
                      'approved'::public.decision_audit_action,
                      'rejected'::public.decision_audit_action
                  )
                ORDER BY created_at DESC
                LIMIT 3
                """,
                (tenant_id,),
            )
            recent_actions = cur.fetchall()

    print(f"tenant_id={tenant_id}")
    print(f"decisions={total} audit_approve_reject={acted} audit_emitted={emitted_audit}")
    for action, reason, ts in recent_actions:
        print(f"  recent: {action} reason_enum={reason} at={ts}")

    if total == 0:
        print("FAIL: no decisions — run scripts/emit_decisions.py", file=sys.stderr)
        return 1
    if acted < 1:
        print(
            "FAIL: no approve/reject audit — run scripts/complete_rm2_gate.py or /inbox",
            file=sys.stderr,
        )
        return 1
    if reject_missing_enum > 0:
        print(
            "FAIL: reject audit rows missing reason_enum (required on reject)",
            file=sys.stderr,
        )
        return 1
    print("rm2_gate=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
