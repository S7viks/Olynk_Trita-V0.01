# Validation Contract

> Written during planning. Never modified to weaken the bar once implementation exists.
> These assertions define what "done" means for this project.

**Pilot tenant:** **Yoga Bar** — use this tenant for all milestone evidence unless a VA explicitly says otherwise.

---

## Core Assertions

### Auth & tenancy (Milestone 1 — RM-0)

- [x] **VA-01:** API derives `tenant_id` only from JWT; body/query tenant override rejected _(pytest `test_tenant_from_jwt.py`; auth exchange routes)_
- [x] **VA-02:** Cross-tenant read/write fails in CI (`F-PLAT-002`) _(RLS migration contract + `.github/workflows/tenant-isolation.yml`)_
- [x] **VA-11:** `.env.example` documents required vars; no secrets committed to git _(pytest `test_env_example.py` + git grep; 2026-05-21 RETRO)_

### Deterministic engine (all milestones)

- [x] **VA-03:** No code path lets LLM compute reorder qty, cover days, or ₹ impact _(pytest `test_llm_draft.py` — system prompt + output pattern guard on `/v1/llm/draft`)_

### Data ingest (Milestone 1 — RM-0)

- [ ] **VA-04:** Shopify webhook HMAC verified; duplicate `(tenant, source, external_id)` is no-op _(deferred — OAuth/sync path; idempotency writer proven)_
- [x] **VA-05:** **Yoga Bar:** Shopify → raw → staging → gold minimal path succeeds _(`verify_rm0_gate.py` + `TRITA_RUN_VA05=1` / dbt contract; 45 raw, 27 dim_sku)_

### Integration health (Milestone 1 — RM-0)

- [x] **VA-06:** Integration health API returns status and last_sync; Sources UI shows Shopify row for Yoga Bar _(pytest `test_integration_health.py`; live row after Shopify sync + migration applied)_

### LLM & metering (Milestone 1 — RM-0)

- [x] **VA-07:** LiteLLM per-tenant budget cap returns fallback, not unbounded completion
- [ ] **VA-08:** OpenMeter receives meter events for LLM usage (`F-PLAT-004`) — **deferred** (not RM-0; no Konnect trial dependency)

### Orchestration (Milestone 1 — RM-0)

- [x] **VA-09:** **Dagster** runs ingest→dbt job once successfully; ADR-001 status **Accepted**
- [ ] **VA-10:** Render health check passes (7d clean post-deploy for demo path) _(deferred — local-first; `render.yaml` + blueprint tests only)_

### Phase 0 negative (Milestone 1 — RM-0)

- [x] **VA-12:** Decision cards are **not** emitted for Yoga Bar in Phase 0 (no premature inbox) _(no `decision*` tables; inbox UI placeholder only)_

### Graph & identity (Milestone 2 — RM-1)

- [x] **VA-13:** **Yoga Bar:** ≥90% order lines resolve to canonical SKU _(2/2 lines, rate=1.0; `verify_rm1_gate.py` + `seed_yoga_bar_shopify_orders.py`)_
- [x] **VA-14:** **Yoga Bar:** Data Health report numbers match gold marts _(dim_sku=27 = feat metrics; `verify_rm1_gate.py`)_

### CSV hub (Milestone 2 — RM-1)

- [x] **VA-26:** **Yoga Bar:** CSV hub ingests end-to-end — known template **or** arbitrary headers with column map → canonical schema validation → valid rows in `raw.csv_hub_events`; invalid rows in quarantine; re-upload same `file_hash` is no-op; Sources health reflects upload outcome (`F-CONN-005`, `P-INGEST-CSV-HUB`) _(3 raw rows, tally healthy; `test_csv_idempotent_replay` + `verify_rm1_gate.py`)_

### Decision inbox (Milestone 3 — RM-2)

- [x] **VA-15:** Dedup `(tenant, type, sku, week)` prevents duplicate cards _(UNIQUE `suppression_key`; `test_decisions.py`)_
- [x] **VA-16:** ≤7 new decision cards per tenant per rolling 7 days _(emitter cap; `test_emit_respects_weekly_cap`)_
- [x] **VA-17:** Stale Shopify or Unicommerce past SLA suppresses inventory decision emit _(integrity module; `test_emit_integrity_suppressed`)_

### Causal (Milestone 4 — RM-3)

- [ ] **VA-18:** No L3 label without DoWhy refutation pass documented
- [ ] **VA-19:** **Yoga Bar:** ≥1 card shows L2 or L3 with evidence refs

### Hardening (Milestone 5 — RM-4)

- [ ] **VA-21:** Sources UI shows **10** integrations with honest status badges for Yoga Bar
- [ ] **VA-22:** Red-team evidence in `docs/ops/`: cross-tenant attempt fails; chat refuses without evidence
- [ ] **VA-23:** Load-test evidence in `docs/ops/`: 10 synthetic tenants meet ingest SLO on staging

### Launch (Milestone 6 — RM-5)

- [ ] **VA-20:** Launch gate checklist complete or waived with sign-off ([LAUNCH-GATE.md](docs/checklists/LAUNCH-GATE.md)) — product ready to ship; commercial rows (paying customer, pilot impact) live in checklist only, not separate VAs

---

## Feature → Assertion Mapping

### Milestone 1 — RM-0

| Feature / task | Must satisfy |
|----------------|--------------|
| Monorepo scaffold | VA-11 |
| F-PLAT-001 Supabase RLS | VA-01, VA-02 |
| F-PLAT-002 + T-P0-003 | VA-02 |
| F-INGEST-SHOPIFY, webhooks | VA-04, VA-05 |
| F-CONN-HEALTH, F-UI-SOURCES-SHELL | VA-06 |
| F-GRAPH-SHELL, dbt shell | VA-05 |
| F-PLAT-003 LiteLLM | VA-03, VA-07 |
| F-PLAT-004 OpenMeter | VA-08 |
| P-ORCH-DAILY-SHELL (Dagster) | VA-09 |
| T-P0-005 Render | VA-10 |
| ADR-001 Dagster | VA-09 |
| RM-0 gate (no inbox) | VA-12 |

### Milestone 2 — RM-1

| Feature area | Must satisfy |
|--------------|--------------|
| F-CONN-002, 004, 006 | VA-05 (per connector), VA-13, VA-14 |
| F-CONN-003 Tally, F-CONN-005 CSV hub, F-CONN-010 Amazon CSV | VA-26, VA-13, VA-14 |
| F-ID-001, F-ID-002 | VA-13 |
| F-METRICS-001..004 | VA-14, VA-03 |
| F-REPORT-HEALTH, F-UI-INVENTORY-LIST, F-UI-SOURCES | VA-14, VA-06 |

### Milestone 3 — RM-2

| Feature area | Must satisfy |
|--------------|--------------|
| F-DEC-001..004 | VA-15, VA-16, VA-17, VA-03 |
| F-DEC-005, F-INBOX-001..004 | VA-15, VA-16 |
| F-DRAFT-001, F-DRAFT-002 | VA-03 |
| RM-2 gate (accept/reject) | VA-15–17 + LAUNCH-GATE product rows at RM-5 via VA-20 |

### Milestone 4 — RM-3

| Feature area | Must satisfy |
|--------------|--------------|
| F-CAUSAL-001..003 | VA-18, VA-19, VA-03 |
| F-PROACTIVE-*, F-CHAT-* | VA-03; chat refusal covered at RM-4 via VA-22 |
| F-CONN-007..009 | VA-05 pattern per connector |

### Milestone 5 — RM-4

| Feature area | Must satisfy |
|--------------|--------------|
| F-GA4, F-CONN-010 | VA-21 |
| F-SEC-001, F-SEC-002 | VA-22 |
| Load / idempotent orchestration | VA-23 |

### Milestone 6 — RM-5

| Feature area | Must satisfy |
|--------------|--------------|
| Launch / billing / legal | VA-20 + all applicable VAs above still true |

---

## Program gates (Milestone Review)

| RM | MISSION | Blocks GO until |
|----|---------|-----------------|
| **RM-0** | 1 | VA-01, VA-02, VA-05, VA-06, VA-07, VA-09, VA-10, VA-11, VA-12 + **ADR-001 Accepted (Dagster)** _(VA-08 deferred)_ |
| **RM-1** | 2 | VA-13, VA-14, VA-26 |
| **RM-2** | 3 | VA-15, VA-16, VA-17 |
| **RM-3** | 4 | VA-18, VA-19 |
| **RM-4** | 5 | VA-21, VA-22, VA-23 |
| **RM-5** | 6 | VA-20 + [LAUNCH-GATE](docs/checklists/LAUNCH-GATE.md) |

Detail: [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## Definition of Done (per feature)

A feature is done when:

1. Its mapped assertions pass
2. No existing assertions are broken
3. A separate agent (not the implementer) has reviewed the code per [`SCRUTINY.md`](SCRUTINY.md)
4. The handoff note is written in [`HANDOFF.md`](HANDOFF.md) (Scrutiny + BEHAVE outcomes when suites exist)
5. Changes are committed to git
