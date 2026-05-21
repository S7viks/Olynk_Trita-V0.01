# Build Order (Ground-Up)

Strict dependency order for solo/small team. **Do not skip** — later items assume earlier contracts.

---

## Layer 0 — Repository bootstrap (Day 1)

| # | Item | Artifact |
|---|------|----------|
| 1 | Monorepo scaffold `trita/` per [README](./README.md) | folders |
| 2 | Supabase project + migrations `tenants`, `memberships` | SQL |
| 3 | CI workflow: lint + tenant isolation placeholder | `.github/workflows` |
| 4 | `.env.example` (no secrets) | template |
| 5 | ADR: Dagster vs Prefect | `docs/adr/001-orchestrator.md` |

---

## Layer 1 — Phase 0 spine (Weeks 1–2)

| # | Item | Feature / Pipeline |
|---|------|-------------------|
| 6 | RLS + JWT FastAPI | F-PLAT-001, F-PLAT-002 |
| 7 | Render deploy stable | T-P0-005 |
| 8 | dlt raw envelope | T-P0-010 |
| 9 | P-INGEST-SHOPIFY | F-INGEST-SHOPIFY |
| 10 | P-WEBHOOK-SHOPIFY | |
| 11 | dbt staging + gold shell | F-GRAPH-SHELL, P-DBT-DAILY |
| 12 | LiteLLM + OpenMeter | F-PLAT-003, F-PLAT-004 |
| 13 | Next auth + Sources shell | F-UI-NAV, F-UI-SOURCES-SHELL |
| 14 | P-ORCH-DAILY-SHELL | |
| 15 | **Gate:** Shopify E2E + health row | Phase 0 exit |

---

## Layer 2 — Phase 1 graph (Weeks 3–5)

| # | Item | Feature / Pipeline |
|---|------|-------------------|
| 16 | Connectors 2–6 ingest | F-CONN-002..006 |
| 17 | CSV hub E2E (validate → raw → quarantine → gold) | F-CONN-005, P-INGEST-CSV-HUB |
| 18 | `packages/ontology` identity v1 | F-ID-001, F-ID-002 |
| 19 | Gold models complete | data-graph.md tables |
| 20 | P-DQ-QUARANTINE + health mart | F-REPORT-HEALTH |
| 21 | P-METRICS-DAILY + INTRADAY | F-METRICS-001..004 |
| 22 | Inventory list UI | F-UI-INVENTORY-LIST |
| 23 | **Gate:** ≥90% order lines + health report | Phase 1 exit |

---

## Layer 3 — Phase 2 inbox (Weeks 6–8)

| # | Item | Feature / Pipeline |
|---|------|-------------------|
| 24 | `packages/decisions` contract + emitter | F-DEC-001..004 |
| 25 | P-DECISION-EMIT | |
| 26 | Suppression + integrity wiring | F-DEC-002, F-DEC-003 |
| 27 | Audit API + table | F-DEC-005 |
| 28 | Inbox UI full | F-INBOX-001..004 |
| 29 | Home feed | F-UI-FEED |
| 30 | Tier-2 drafts | F-DRAFT-001, F-DRAFT-002 |
| 31 | Reports 3 inventory + outcomes | F-REPORT-*, P-OUTCOME-EVAL |
| 32 | Settings lead times | F-SETTINGS-001 |
| 33 | **Gate:** pilot accept/reject ≥1 | Phase 2 exit |

---

## Layer 4 — Phase 3 intelligence (Weeks 9–11)

| # | Item | Feature / Pipeline |
|---|------|-------------------|
| 34 | Connectors 7–9 | F-CONN-007..009 |
| 35 | P-FEAT-MATRIX-WEEKLY | F-FEAT-MATRIX |
| 36 | P-CAUSAL-ASSOC | F-CAUSAL-001 |
| 37 | P-CAUSAL-DOWHY | F-CAUSAL-002 |
| 38 | Causal on cards + copy | F-CAUSAL-003 |
| 39 | Proactive triggers + feed | F-PROACTIVE-001,002 |
| 40 | Email + Slack digest | F-PROACTIVE-003,004 |
| 41 | Chat API + UI | F-CHAT-001,002 |
| 42 | **Gate:** L2/L3 on one pilot card | Phase 3 exit |

---

## Layer 5 — Phase 4–5 production (Weeks 12–16)

| # | Item | Feature / Pipeline |
|---|------|-------------------|
| 43 | GA4 + Amazon | F-GA4, F-CONN-010 |
| 44 | Idempotent orchestration audit | T-P4-010 |
| 45 | Load + red team | F-SEC-001,002 |
| 46 | Evidence pack + economics dash | F-OPS-001,002 |
| 47 | Legal + billing + onboarding | F-LEGAL-*, F-BILLING-001 |
| 48 | Launch gate review | LAUNCH-GATE.md |
| 49 | **Gate:** paid customer | Phase 5 exit |

---

## Critical path (cannot parallelize easily)

```
RLS → Shopify ingest → dbt gold → identity → metrics → decisions → inbox UI
                                                      ↘ causal → card copy
```

**Safe parallel tracks after Week 2:**

- Frontend polish vs connector 2–6
- OpenMeter dashboard vs dbt models
- Legal docs vs Phase 3 causal (Week 9+)

---

## Definition of "done" per layer

Each item is done only when:

1. Acceptance criteria in [features/REGISTRY.md](./features/REGISTRY.md) met
2. Tenant isolation test covers new tables/APIs
3. Pipeline listed in [pipelines/REGISTRY.md](./pipelines/REGISTRY.md) runs in staging
4. No `service_role` bypass without `tenant_id` filter
