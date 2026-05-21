# Orchestrator — Worker Procedures

Routing for **worker** (implementer) and **scrutiny** (reviewer) agents. Product truth remains in [`docs/context/MASTER-CONTEXT.md`](docs/context/MASTER-CONTEXT.md).

**Cursor multi-chat workflow** (triggers `SHIP`, `SCRUTINY`, `BEHAVE`, …): [`docs/CURSOR-MULTI-AGENT-WORKFLOW.md`](docs/CURSOR-MULTI-AGENT-WORKFLOW.md).  
**Reading order hub:** [`docs/DOCUMENTATION_INDEX.md`](docs/DOCUMENTATION_INDEX.md).

---

## Read order (every worker session)

1. [`MISSION.md`](MISSION.md) — goal, active milestone, feature priority
2. [`VALIDATION.md`](VALIDATION.md) — assertions that define done for the active feature
3. [`docs/ROADMAP.md`](docs/ROADMAP.md) — RM gate for current phase
4. Phase file under [`docs/roadmap/`](docs/roadmap/) — task IDs `T-P{n}-*`
5. Feature spec from [`docs/features/REGISTRY.md`](docs/features/REGISTRY.md)
6. [`docs/BUILD-ORDER.md`](docs/BUILD-ORDER.md) — do not skip dependencies

---

## Role boundaries

Logical agents per [`docs/context/agents.md`](docs/context/agents.md):

| Role | Must | Must NOT |
|------|------|----------|
| Implementer | Satisfy mapped VAs; update feature registry status | Weaken VALIDATION; bypass tenant_id from JWT; ship connector/CSV **stubs** (upload without raw+quarantine) |
| AG-INV path | Deterministic inventory math | LLM for qty, cover, ₹ |
| AG-DEC path | Suppression, integrity gates | Emit on stale Shopify/Unicommerce |
| AG-ACT | Tier-2 drafts on approve | Tier-3 writes to external systems |
| Reviewer | Run [`SCRUTINY.md`](SCRUTINY.md) checklist | Be the same session that implemented (separate agent) |

---

## Per-feature workflow

1. **Pick** next unchecked feature in MISSION for current milestone.
2. **Map** feature → VAs in VALIDATION; note RM gate if phase exit.
3. **Implement** minimal diff; match repo conventions when `trita/` exists.
4. **Test** commands from [`tests/BEHAVE.md`](tests/BEHAVE.md) for mapped VAs (when suites exist).
5. **Handoff** — append section to [`HANDOFF.md`](HANDOFF.md):
   - Status, commit hash, commands + exit codes
   - VAs satisfied / deferred
   - Notes for next worker
6. **Scrutiny** — separate agent records verdict in HANDOFF (Scrutiny section).
7. **Commit** — only after scrutiny PASS (or documented waiver).
8. **Log** — append [`MISSION_LOG.md`](MISSION_LOG.md).

---

## Integrity abort (stop-the-line)

Halt feature work and fix before continuing (from [`docs/checklists/phase-exit-criteria.md`](docs/checklists/phase-exit-criteria.md)):

| Condition | Action |
|-----------|--------|
| Cross-tenant data in test | Fix isolation first |
| LLM computed reorder qty shipped | Patch deterministic path |
| L3 shown without refutation pass | Patch causal promotion |
| >7 cards/week without cap | Patch suppression |
| Tier 3 external write enabled | Disable flag immediately |

---

## Milestone review

Before advancing **MISSION** milestone number:

1. All features for that milestone checked in MISSION.md
2. All Milestone-mapped VAs checked in VALIDATION.md
3. RM-* row for phase shows GO in ROADMAP.md
4. Phase exit evidence in HANDOFF or `docs/ops/` as applicable

---

## LLM routing (reference)

| Task | Model | Notes |
|------|-------|-------|
| Card copy, causal narrative | Gemini | Schema-bound |
| Chat Q&A | Groq | Inventory-scoped |
| PO / email draft | Gemini | Tier 2 only |

See [`docs/context/stack-oss.md`](docs/context/stack-oss.md).
