"""Causal pipeline orchestration (P-CAUSAL-ASSOC + P-CAUSAL-DOWHY)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_causal.association import scan_associations
from trita_causal.db import upsert_edge
from trita_causal.dowhy_runner import promote_associations
from trita_causal.labels import narrative_for_edge
from trita_causal.matrix import load_sku_matrices
from trita_causal.policy import load_policy


def run_causal_pipeline(conn, tenant_id: UUID) -> dict[str, Any]:
    """
    Association scan → DoWhy refutation → persist analytics.causal_edges.
    Deterministic; no LLM inventory math.
    """
    policy = load_policy()
    max_skus = int(policy.get("max_skus_per_run", 500))
    edges_written = 0
    skus_processed = 0
    l1_count = 0
    l2_count = 0
    l3_count = 0

    with conn.cursor() as cur:
        matrices = load_sku_matrices(cur, tenant_id, max_skus=max_skus)
        for matrix in matrices:
            skus_processed += 1
            assoc = scan_associations(matrix)
            if not assoc:
                continue
            promoted = promote_associations(matrix, assoc)
            for edge in promoted:
                edge.narrative = narrative_for_edge(edge)
                if edge.epistemic_layer == "L1":
                    l1_count += 1
                elif edge.epistemic_layer == "L2":
                    l2_count += 1
                elif edge.epistemic_layer == "L3":
                    l3_count += 1
                upsert_edge(cur, edge)
                edges_written += 1

    return {
        "tenant_id": str(tenant_id),
        "skus_processed": skus_processed,
        "edges_written": edges_written,
        "l1": l1_count,
        "l2": l2_count,
        "l3": l3_count,
    }
