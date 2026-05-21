# Phase Exit Criteria (Summary)

Quick gate table — detail in phase roadmap files.

| Phase | Week | Exit test | Evidence artifact |
|-------|------|-----------|-------------------|
| **0** | 2 | Test tenant: Shopify → raw → gold; health row green | Screenshot + CI log |
| **1** | 5 | Pilot Data Health Report accurate; ≥90% order lines resolved | Report export + SQL metric |
| **2** | 8 | Pilot accept/reject ≥1 card with reason; ≤7 cards/week test | Audit log row |
| **3** | 11 | ≥1 card with L2 or L3 driver + evidence | Card JSON + screenshot |
| **4** | 14 | 10 sources in UI; red team + load test docs | Reports in `docs/ops/` |
| **5** | 16 | Launch gate pass; ≥1 paying @ ₹10K+ | Invoice or contract |

---

## Stop-the-line conditions (any phase)

| Condition | Action |
|-----------|--------|
| Cross-tenant data in test | Halt feature work; fix isolation |
| LLM computed reorder qty shipped | Halt; patch deterministic path |
| L3 shown without refutation pass | Halt; patch causal promotion |
| >7 cards/week without cap | Halt; patch suppression |
| Tier 3 external write enabled | Disable flag immediately |

---

## Weekly ritual (recommended)

1. Review [features/REGISTRY.md](../features/REGISTRY.md) status column
2. Run orchestrator in staging; check quarantine counts
3. OpenMeter: LLM cost % of pilot MRR proxy
4. Pilot evidence pack draft (from Phase 2 onward)
5. Update phase exit evidence row
