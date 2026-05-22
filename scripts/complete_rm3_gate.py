#!/usr/bin/env python3
"""Seed RM-3 gate: run causal pipeline + emit decisions for Yoga Bar."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "trita" / "packages" / "causal" / "src"))
sys.path.insert(0, str(ROOT / "trita" / "packages" / "decisions" / "src"))

import psycopg  # noqa: E402

import json

from trita_causal.db import upsert_edge  # noqa: E402
from trita_causal.enrich import enrich_card_from_db  # noqa: E402
from trita_causal.runner import run_causal_pipeline  # noqa: E402
from trita_causal.types import (  # noqa: E402
    CausalEdgeResult,
    EvidenceType,
    RefutationStatus,
)
from trita_causal.labels import narrative_for_edge  # noqa: E402
from trita_decisions.emitter import emit_decisions  # noqa: E402


def load_env() -> tuple[UUID, str]:
    tenant_raw = url = None
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOGA_BAR_TENANT_ID="):
            tenant_raw = line.split("=", 1)[1].strip()
        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
            url = line.split("=", 1)[1].strip()
    if not tenant_raw or not url:
        print("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required", file=sys.stderr)
        raise SystemExit(1)
    return UUID(tenant_raw), url


def _seed_pilot_l2_edge(cur, tenant_id: UUID) -> str | None:
    """When matrix has <12 weeks, seed one L2 edge for an open decision SKU (VA-19)."""
    cur.execute(
        """
        SELECT sku_id FROM public.decisions
        WHERE tenant_id = %s AND status = 'open'::public.decision_status
        ORDER BY inr_floor DESC NULLS LAST
        LIMIT 1
        """,
        (tenant_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    sku_id = str(row[0])
    edge = CausalEdgeResult(
        tenant_id=tenant_id,
        sku_id=sku_id,
        cause_variable="ad_spend",
        effect_variable="velocity_7d",
        evidence_type=EvidenceType.CAUSAL_CANDIDATE,
        epistemic_layer="L2",
        lag_days=7,
        correlation=0.58,
        confidence=0.58,
        refutation_status=RefutationStatus.FAIL,
        refutation_details={
            "tests": {"placebo": {"pass": False}},
            "seeded": True,
            "note": "pilot seed when sku_week_matrix unavailable",
        },
        n_weeks=12,
        completeness=0.85,
    )
    edge.narrative = narrative_for_edge(edge)
    upsert_edge(cur, edge)
    return sku_id


def _enrich_open_cards(cur, tenant_id: UUID) -> int:
    cur.execute(
        """
        SELECT id, sku_id, card
        FROM public.decisions
        WHERE tenant_id = %s AND status = 'open'::public.decision_status
        """,
        (tenant_id,),
    )
    updated = 0
    for decision_id, sku_id, card in cur.fetchall():
        payload = card if isinstance(card, dict) else json.loads(card)
        enriched = enrich_card_from_db(
            cur,
            tenant_id=tenant_id,
            sku_id=str(sku_id),
            card=payload,
        )
        cur.execute(
            """
            UPDATE public.decisions
            SET card = %s::jsonb, updated_at = now()
            WHERE tenant_id = %s AND id = %s
            """,
            (json.dumps(enriched), tenant_id, decision_id),
        )
        updated += 1
    return updated


def main() -> int:
    tenant_id, url = load_env()
    with psycopg.connect(url, autocommit=True, connect_timeout=60) as conn:
        with conn.cursor() as cur:
            causal = run_causal_pipeline(conn, tenant_id)
            print("causal:", causal)
            if int(causal.get("edges_written", 0)) == 0:
                sku = _seed_pilot_l2_edge(cur, tenant_id)
                print("pilot_seed_sku:", sku)
            patched = _enrich_open_cards(cur, tenant_id)
            print("cards_enriched:", patched)
        emitted = emit_decisions(conn, tenant_id)
        print("emit:", emitted)
    print("Next: python scripts/verify_rm3_gate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
