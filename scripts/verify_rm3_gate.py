#!/usr/bin/env python3
"""RM-3 gate: Yoga Bar has >=1 decision card with L2/L3 + causal evidence (VA-19)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "trita" / "packages" / "decisions" / "src"))
sys.path.insert(0, str(ROOT / "trita" / "packages" / "causal" / "src"))

try:
    import psycopg
except ImportError:
    print("FAIL: psycopg required")
    sys.exit(1)

def load_env() -> tuple[str, str]:
    tenant_raw = url = None
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("YOGA_BAR_TENANT_ID="):
                tenant_raw = line.split("=", 1)[1].strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                url = line.split("=", 1)[1].strip()
    tenant_raw = tenant_raw or os.environ.get(
        "YOGA_BAR_TENANT_ID",
        os.environ.get("TRITA_PILOT_TENANT_ID", "11111111-1111-1111-1111-111111111101"),
    )
    url = url or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not url:
        print("FAIL: YOGA_BAR_TENANT_ID and DATABASE_URL required", file=sys.stderr)
        raise SystemExit(1)
    return tenant_raw, url


def main() -> int:
    tenant_id, url = load_env()

    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT card
                FROM public.decisions
                WHERE tenant_id = %s::uuid
                ORDER BY created_at DESC
                LIMIT 200
                """,
                (tenant_id,),
            )
            rows = cur.fetchall()

    l2_l3 = 0
    with_causal_ref = 0
    l3_without_pass = 0
    exemplar: dict[str, object] | None = None

    for (card,) in rows:
        if not isinstance(card, dict):
            card = json.loads(card) if isinstance(card, str) else {}
        reasoning = card.get("reasoning") or {}
        layer = str(reasoning.get("epistemic_layer", "L0"))
        refs = reasoning.get("evidence_refs") or []
        chain = reasoning.get("causal_chain") or []
        has_causal_ref = any(
            isinstance(r, str) and r.startswith("analytics.causal_edges:") for r in refs
        )
        if layer in ("L2", "L3"):
            l2_l3 += 1
        if has_causal_ref or chain:
            with_causal_ref += 1
        if (
            exemplar is None
            and layer in ("L2", "L3")
            and (has_causal_ref or chain)
        ):
            exemplar = {
                "epistemic_layer": layer,
                "evidence_refs": refs[:5],
                "causal_chain_len": len(chain),
            }
        for link in chain:
            if not isinstance(link, dict):
                continue
            if link.get("layer") == "L3" and link.get("refutation_status") != "pass":
                l3_without_pass += 1

    print(f"decisions_scanned={len(rows)}")
    print(f"cards_l2_l3={l2_l3}")
    print(f"cards_with_causal_evidence={with_causal_ref}")
    print(f"l3_ui_without_pass={l3_without_pass}")

    if l3_without_pass > 0:
        print("FAIL: VA-18 — L3 shown without refutation pass")
        return 1
    if l2_l3 < 1 or with_causal_ref < 1:
        print("FAIL: VA-19 — need >=1 Yoga Bar card with L2/L3 and causal evidence refs")
        return 1

    if exemplar:
        print(f"exemplar={json.dumps(exemplar, default=str)}")
    print("PASS: RM-3 causal gate (VA-18, VA-19)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
