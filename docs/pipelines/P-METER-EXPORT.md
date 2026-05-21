# Pipeline: P-METER-EXPORT

> **Status: DEFERRED** — not RM-0. No runtime ingest in Phase 0. See [F-PLAT-004](../features/REGISTRY.md).

**Phase:** 4+ (scheduled flush)  
**Feature:** F-PLAT-004  
**Task:** T-P0-032 / **VA-08** (when unit economics ships)

---

## Purpose

Emit usage events to [OpenMeter](https://openmeter.io/docs/metering/events/overview) for unit economics. Phase 0 uses **synchronous ingest** on hot paths; batch export cron is later.

---

## Meters (event `type` = meter slug)

| Meter | Emitter | When |
|-------|---------|------|
| `llm_requests` | `trita_api.metering.emit_llm_usage` | Successful LiteLLM completion |
| `llm_tokens_in` | same | `prompt_tokens` > 0 |
| `llm_tokens_out` | same | `completion_tokens` > 0 |
| `connector_sync_rows` | `emit_connector_sync` | Shopify sync success |
| `connector_api_calls` | same | Per sync (3 Admin API calls) |
| `dbt_run_seconds` | `emit_dbt_run` | `scripts/run_dbt.py` or Dagster `dbt_run_op` |

`subject` = tenant UUID string (or `platform` for dbt without tenant).

---

## Config

| Env | Purpose |
|-----|---------|
| `OPENMETER_URL` | Base URL, e.g. `https://openmeter.cloud` |
| `OPENMETER_API_KEY` | Bearer token for ingest |

If unset, emit functions no-op (local dev without metering).

---

## Dashboard setup (OpenMeter Cloud)

Create meters matching event types above; aggregation `SUM` on `$.value`. See [trita/services/openmeter/README.md](../../trita/services/openmeter/README.md).

---

## Done when (T-P0-032 / VA-08)

- API emits CloudEvents on LLM + connector paths when env configured
- pytest `test_openmeter.py` green
- Optional live: `TRITA_RUN_VA08=1` with real keys — event visible in OpenMeter UI
