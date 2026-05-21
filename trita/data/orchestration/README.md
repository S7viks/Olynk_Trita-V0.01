# data/orchestration

Dagster code location per **ADR-001 Accepted** ([docs/adr/001-orchestrator.md](../../../docs/adr/001-orchestrator.md)).

| Task | Status |
|------|--------|
| T-P0-050 — ADR recorded | Done |
| T-P0-051 — `P-ORCH-DAILY-SHELL` | Done — `daily_shell_job` — [spec](../../../docs/pipelines/P-ORCH-DAILY-SHELL.md) |

## Job: `daily_shell_job`

1. **shopify_sync_op** — Shopify → `raw.shopify_events` (pilot `YOGA_BAR_TENANT_ID` only)
2. **dbt_run_op** — `scripts/run_dbt.py run`
3. **integration_health_op** — asserts raw + `gold.dim_sku` row counts > 0

## Install

```bash
cd trita/data/orchestration
pip install -e .
pip install -e ../dlt
pip install -e ../../apps/api
```

API + dlt editable installs are required for **direct** ingest (default). Use `TRITA_ORCH_INGEST_MODE=api` to call FastAPI instead (API must be running).

## Run once (VA-09)

From repo root:

```bash
python scripts/run_daily_shell.py
```

Or:

```bash
cd trita/data/orchestration
dagster job execute -m trita_orchestration -j daily_shell_job
```

## Env

| Variable | Purpose |
|----------|---------|
| `YOGA_BAR_TENANT_ID` | Pilot partition (required) |
| `DATABASE_URL` | Ingest + dbt + health check |
| `TRITA_ORCH_INGEST_MODE` | `direct` (default) or `api` |
| `TRITA_RUN_VA09` | Set `1` to run live integration test |

Do not add cron ingest→dbt outside Dagster without a new ADR.
