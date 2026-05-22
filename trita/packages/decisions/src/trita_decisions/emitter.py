"""Decision emit orchestration (F-DEC-001..004)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

EMIT_AUDIT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

import psycopg

from trita_decisions.candidates import build_candidates, load_latest_metrics
from trita_decisions.audit import append_audit
from trita_decisions.db import insert_decision
from trita_decisions.integrity import check_integrity_suppress
from trita_decisions.suppression import (
    remaining_weekly_quota,
    suppression_key_exists,
)


def emit_decisions(conn, tenant_id: UUID) -> dict[str, Any]:
    """
    Emit inventory decision cards for tenant.
    Deterministic metrics only; no LLM qty/₹ math.
    """
    emitted = 0
    skipped_dedup = 0
    skipped_cap = 0
    candidates_count = 0

    with conn.cursor() as cur:
        suppressed, source = check_integrity_suppress(cur, tenant_id)
        if suppressed:
            return {
                "tenant_id": str(tenant_id),
                "emitted": 0,
                "skipped_dedup": 0,
                "skipped_cap": 0,
                "integrity_suppressed": True,
                "integrity_source": source,
                "candidates_considered": 0,
            }

        snapshots = load_latest_metrics(cur, tenant_id)
        candidates = build_candidates(snapshots)
        candidates_count = len(candidates)
        quota = remaining_weekly_quota(cur, tenant_id)

        for candidate in candidates:
            try:
                from trita_causal.enrich import enrich_candidate_card

                enrich_candidate_card(cur, candidate)
            except ImportError:
                pass
            except Exception:
                pass

            if quota <= 0:
                skipped_cap += 1
                continue
            if suppression_key_exists(cur, tenant_id, candidate.suppression):
                skipped_dedup += 1
                continue
            if insert_decision(cur, candidate):
                append_audit(
                    cur,
                    tenant_id=tenant_id,
                    decision_id=UUID(str(candidate.card["id"])),
                    user_id=EMIT_AUDIT_USER_ID,
                    action="emitted",
                    projection_hash=candidate.projection,
                )
                emitted += 1
                quota -= 1
            else:
                skipped_dedup += 1

    return {
        "tenant_id": str(tenant_id),
        "emitted": emitted,
        "skipped_dedup": skipped_dedup,
        "skipped_cap": skipped_cap,
        "integrity_suppressed": False,
        "candidates_considered": candidates_count,
    }
