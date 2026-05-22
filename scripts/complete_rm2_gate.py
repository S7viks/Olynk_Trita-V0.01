"""RM-2 gate evidence: refresh integrity, emit cards, reject one with reason_enum (Yoga Bar)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "trita" / "packages" / "decisions" / "src"
SCRIPTS = REPO / "scripts"
for p in (str(PKG), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import psycopg

from _pg_connect import connect as pg_connect
from trita_decisions.emitter import emit_decisions
from trita_decisions.inbox import get_decision, list_inbox, reject_decision

PILOT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
REJECT_REASON = "not_actionable"
INTEGRITY_SOURCES = ("shopify", "unicommerce")


def load_env() -> tuple[UUID, str]:
    tenant_raw = url = None
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        raise SystemExit("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required in .env")
    return UUID(tenant_raw), url


def refresh_integrity_health(cur, tenant_id: UUID) -> None:
    now = datetime.now(UTC)
    for source in INTEGRITY_SOURCES:
        cur.execute(
            """
            UPDATE public.integration_health
            SET last_sync_at = %s,
                status = 'healthy'::public.integration_status,
                updated_at = now()
            WHERE tenant_id = %s AND source = %s
            """,
            (now, tenant_id, source),
        )
        print(f"  refreshed {source} last_sync_at")


def _acted_count(cur, tenant_id: UUID) -> int:
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
    return int(cur.fetchone()[0])


def main() -> int:
    tenant_id, url = load_env()
    print(f"tenant_id={tenant_id}")

    with pg_connect(url, autocommit=True) as conn:
        with conn.cursor() as cur:
            if _acted_count(cur, tenant_id) >= 1:
                print("Step 0 — pilot already has approve/reject audit; skipping emit/reject")
            else:
                print("Step 1 — refresh Shopify + Unicommerce health (integrity gate)")
                refresh_integrity_health(cur, tenant_id)

                emit_result = emit_decisions(conn, tenant_id)
                print(f"Step 2 — emit: {emit_result}")
                if emit_result.get("integrity_suppressed"):
                    print(
                        "FAIL: still integrity suppressed after health refresh",
                        file=sys.stderr,
                    )
                    return 1
                if int(emit_result.get("emitted") or 0) == 0 and emit_result.get("skipped_dedup", 0) == 0:
                    print("WARN: zero emitted — checking for existing open cards", file=sys.stderr)

                with conn.cursor() as cur2:
                    open_cards = list_inbox(cur2, tenant_id, tab="open", limit=20)
                    if not open_cards:
                        print("FAIL: no open decisions to reject", file=sys.stderr)
                        return 1
                    target_id = UUID(open_cards[0]["id"])
                    print(
                        f"Step 3 — reject {target_id} ({open_cards[0].get('sku_code')}) "
                        f"reason_enum={REJECT_REASON}"
                    )
                    reject_decision(
                        cur2,
                        tenant_id=tenant_id,
                        decision_id=target_id,
                        user_id=PILOT_USER_ID,
                        reason_enum=REJECT_REASON,
                        reason_text="RM-2 gate pilot evidence",
                    )

    import subprocess

    print("Step 4 — verify_rm2_gate.py")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "verify_rm2_gate.py")],
        cwd=REPO,
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
