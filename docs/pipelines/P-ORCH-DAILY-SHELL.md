# Pipeline: P-ORCH-DAILY-SHELL

**Phase:** 0  
**Orchestrator:** Dagster (ADR-001 Accepted, T-P0-050)  
**Task:** T-P0-051 — first runtime proof (VA-09)

---

## Purpose

Single manual Dagster job chaining **Shopify ingest → dbt** for pilot tenant Yoga Bar. Proves ADR-001 is operable before full `P-ORCH-DAILY` schedules.

---

## Job graph (target)

```mermaid
flowchart LR
  A[shopify_sync op] --> B[dbt_run op]
  B --> C[integration_health op]
```

| Step | Implementation (Phase 0) | Output |
|------|---------------------------|--------|
| 1 | API `POST /v1/sources/shopify/sync` or dlt CLI | `raw.shopify_events` |
| 2 | `python scripts/run_dbt.py run` | `staging.*`, `gold.*` |
| 3 | (later) health mart row | `feat.integration_health` |

---

## Idempotency

- Ingest: `(tenant, source, external_id, entity_type)` dedup in raw
- dbt: incremental models / full-refresh views acceptable in shell

---

## Config

| Env | Use |
|-----|-----|
| `YOGA_BAR_TENANT_ID` | Partition key for pilot |
| `DATABASE_URL` | dbt + ingest |
| Dagster run config | `tenant_id` must match JWT tenant — never from untrusted body |

---

## Done when (T-P0-051 / VA-09)

- `dagster job execute` (or UI) completes once in dev/staging
- Yoga Bar: raw row count > 0 and `gold.dim_sku` row count > 0 after chain
- Documented command in HANDOFF with exit code 0

**Not in T-P0-050:** This spec only; code lands under `trita/data/orchestration/` in T-P0-051.

---

## Implementation (T-P0-051)

| Artifact | Role |
|----------|------|
| `trita/data/orchestration/src/trita_orchestration/` | Dagster ops + `daily_shell_job` |
| `scripts/run_daily_shell.py` | `execute_in_process` wrapper (VA-09 proof) |
| `trita/data/orchestration/README.md` | Install + run commands |

**Run once:**

```bash
python scripts/run_daily_shell.py
# or: cd trita/data/orchestration && dagster job execute -m trita_orchestration -j daily_shell_job
```

Default ingest: `TRITA_ORCH_INGEST_MODE=direct` (in-process, no API). Set `api` to use `POST /v1/sources/shopify/sync`.
