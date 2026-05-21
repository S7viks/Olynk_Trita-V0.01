# Phase 0 — Spine (Weeks 1–2)

**Goal:** Safe substrate before intelligence. No pilot decisions until exit criteria met.

**Exit:** **Yoga Bar** ingests Shopify end-to-end with integration health card visible.

---

## Work packages

### WP0-A — Tenant isolation & API substrate


| Task ID  | Task                                    | Owner   | Depends  | Done when                           |
| -------- | --------------------------------------- | ------- | -------- | ----------------------------------- |
| T-P0-001 | Supabase project + Auth + RLS baseline  | Backend | —        | `tenant`, `membership` tables + RLS |
| T-P0-002 | Tenant isolation test suite in CI       | Backend | T-P0-001 | Cross-tenant read/write fails       |
| T-P0-003 | Audit `service_role` paths; fix leaks   | Backend | T-P0-002 | CI green                            |
| T-P0-004 | FastAPI scaffold + JWT middleware       | Backend | T-P0-001 | `tenant_id` from token only         |
| T-P0-005 | Render deploy (paid tier, health check) | Infra   | T-P0-004 | No 502 on demo path                 |


**Features:** `F-PLAT-001`, `F-PLAT-002`

---

### WP0-B — Data ingest skeleton


| Task ID  | Task                                        | Owner   | Depends  | Done when                          |
| -------- | ------------------------------------------- | ------- | -------- | ---------------------------------- |
| T-P0-010 | `data/dlt` project + raw envelope schema    | Data    | —        | `raw.{source}` with hash + lineage |
| T-P0-011 | Shopify tap (orders + inventory)            | Data    | T-P0-010 | First load to raw                  |
| T-P0-012 | Webhook receiver stub (Shopify)             | Backend | T-P0-011 | HMAC verified → queue              |
| T-P0-013 | Idempotency `(tenant, source, external_id)` | Data    | T-P0-010 | Duplicate webhook no-op            |


**Features:** `F-INGEST-SHOPIFY`, `F-CONN-SHOPIFY`  
**Pipelines:** `P-INGEST-SHOPIFY`, `P-WEBHOOK-SHOPIFY`

---

### WP0-C — Transform skeleton


| Task ID  | Task                                             | Owner | Depends  | Done when               |
| -------- | ------------------------------------------------ | ----- | -------- | ----------------------- |
| T-P0-020 | `data/dbt` project init                          | Data  | T-P0-011 | `staging` models run    |
| T-P0-021 | Gold shell tables (`dim_sku`, `fact_order_line`) | Data  | T-P0-020 | Empty graph queryable   |
| T-P0-022 | dbt-expectations on staging                      | Data  | T-P0-020 | Quarantine model exists |


**Pipelines:** `P-DBT-DAILY`

---

### WP0-D — LLM & metering


| Task ID  | Task                                 | Owner    | Depends  | Done when                   |
| -------- | ------------------------------------ | -------- | -------- | --------------------------- |
| T-P0-030 | LiteLLM proxy deploy (Gemini + Groq) | Backend  | —        | Health + test completion    |
| T-P0-031 | Per-tenant budget config             | Backend  | T-P0-030 | Hard cap returns fallback   |
| T-P0-032 | OpenMeter meters wired               | Platform | T-P0-030 | Events visible in dashboard |
| T-P0-033 | OTEL basic traces api ↔ llm          | Platform | T-P0-004 | Trace in collector          |


**Features:** `F-PLAT-003`, `F-PLAT-004`  
**Pipelines:** `P-LLM-PROXY`, `P-METER-EXPORT`

---

### WP0-E — Web shell


| Task ID  | Task                             | Owner    | Depends  | Done when                |
| -------- | -------------------------------- | -------- | -------- | ------------------------ |
| T-P0-040 | Next.js app + auth flow          | Frontend | T-P0-001 | Login → tenant context   |
| T-P0-041 | Sources page shell (health rows) | Frontend | T-P0-004 | Shopify row shows status |
| T-P0-042 | Navigation scaffold (7 routes)   | Frontend | T-P0-040 | Routes match product map |


**Features:** `F-UI-NAV`, `F-UI-SOURCES-SHELL`

---

### WP0-F — Orchestration


| Task ID  | Task                              | Owner | Depends            | Done when               |
| -------- | --------------------------------- | ----- | ------------------ | ----------------------- |
| T-P0-050 | Dagster chosen (ADR-001 Accepted) | Data  | —                  | ADR recorded            |
| T-P0-051 | Single job: ingest → dbt          | Data  | T-P0-011, T-P0-020 | Manual trigger succeeds |


**Pipelines:** `P-ORCH-DAILY-SHELL`

---

## Deliverables checklist

- CI: tenant isolation green
- Shopify → raw → staging → gold (minimal)
- Integration health API + UI row
- LiteLLM + OpenMeter events
- Render stable for demo
- Orchestrator runs one pipeline

---

## Do not start in Phase 0

- Decision inbox logic
- DoWhy / causal
- Non-Shopify connectors and CSV hub (RM-1 only — production ingest, no stubs)
- Billing

---

## References

- [../context/architecture.md](../context/architecture.md)
- [../pipelines/P-INGEST-SHOPIFY.md](../pipelines/P-INGEST-SHOPIFY.md)
- [../BUILD-ORDER.md](../BUILD-ORDER.md) — items 1–15

