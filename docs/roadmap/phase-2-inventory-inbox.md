# Phase 2 — Inventory Inbox (Weeks 6–8)

**Status (2026-05-22):** **Closed** — RM-2 GO; evidence `scripts/verify_rm2_gate.py` (VA-15–17, RM-2 gate). See [HANDOFF.md](../../HANDOFF.md) RETRO Milestone 3.

**Goal:** Closed loop on web — surface, approve/reject, audit, draft, outcomes.

**Exit:** Pilot accepts or rejects ≥1 card with reason; suppression verified.

---

## Work packages

### WP2-A — Decision engine

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P2-001 | Card emitter: REORDER, DEAD, CAPITAL, BLOCKED | Types match contract |
| T-P2-002 | ₹ impact floor engine (conservative) | Methodology doc linked |
| T-P2-003 | Suppression: dedup + 7/week cap | Test fixtures pass |
| T-P2-004 | Integrity suppress wiring | Stale Shopify/Uni blocks emit |
| T-P2-005 | `projection_hash` on emit | Audit reproducible |

**Features:** `F-DEC-001`..`F-DEC-006`  
**Package:** `packages/decisions/`  
**Pipelines:** `P-DECISION-EMIT`

---

### WP2-B — Decision Inbox UI

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P2-010 | Inbox list + filters (type, SKU, status) | Primary nav works |
| T-P2-011 | Card detail: impact, reasoning, evidence links | L0 facts visible |
| T-P2-012 | Accept / reject / snooze | Enum reasons required |
| T-P2-013 | Timeline per decision | Audit entries shown |
| T-P2-014 | Home proactive feed (subset of inbox) | Today's attention |

**Features:** `F-INBOX-001`..`F-INBOX-005`, `F-UI-FEED`

---

### WP2-C — Tier-2 drafts

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P2-020 | PO draft schema + Gemini generation | Schema validation |
| T-P2-021 | Supplier email draft | On approve → artifact |
| T-P2-022 | Artifacts stored + linked in timeline | Download / copy |

**Features:** `F-DRAFT-001`, `F-DRAFT-002`  
**Agent:** `AG-ACT`

---

### WP2-D — Outcomes & reports

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P2-030 | Outcome jobs T+7, T+14 | Scheduler runs |
| T-P2-031 | Report: SKU aging (₹ sort) | Matches metrics |
| T-P2-032 | Report: dead stock list | Matches D-DEAD |
| T-P2-033 | Report: reorder queue | Matches D-REORDER |
| T-P2-034 | Evidence refs drill-down | Click → source row |

**Features:** `F-REPORT-AGING`, `F-REPORT-DEAD`, `F-REPORT-REORDER`  
**Pipelines:** `P-OUTCOME-EVAL`

---

### WP2-E — Settings

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P2-040 | Lead times per supplier/SKU default | Used in reorder_qty |
| T-P2-041 | Notification prefs shell | Email Phase 3 |

**Features:** `F-SETTINGS-001`

---

## Card generation rules (implementation checklist)

| Type | Condition | Blocked if |
|------|-----------|------------|
| REORDER | `stockout_risk` | integrity suppress |
| DEAD | `dead_stock` | — |
| CAPITAL | capital_at_risk > threshold | COGS missing → lower priority only |
| BLOCKED | unresolved SKU, missing COGS for ₹ | — |

---

## Deliverables checklist

- [x] Cards on pilot + fixtures
- [x] Inbox accept/reject/snooze + audit
- [x] ≤7 cards/week verified
- [x] Tier-2 draft on approve
- [ ] 4 reports (incl. health from P1) — health from P1; aging/dead/reorder deferred
- [ ] Outcome scheduler running — `F-DEC-006` deferred
- [x] Pilot sign-off: ≥1 decision action

---

## References

- [../context/decision-contract.md](../context/decision-contract.md)
- [../features/decision-inbox.md](../features/decision-inbox.md)
