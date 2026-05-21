# Trita monorepo

Application code for **Trita V0.0.1** (OLynk). Planning docs live in the repo root `docs/`.

## Layout

| Path | Role |
|------|------|
| `apps/web` | Next.js 14 (Vercel) |
| `apps/api` | FastAPI (Render) |
| `data/dlt` | dlt ingest taps |
| `data/dbt` | dbt transforms |
| `data/orchestration` | Dagster code location (ADR-001) |
| `packages/ontology` | Commerce graph + identity |
| `packages/decisions` | Decision contract, suppression, audit |
| `packages/causal` | Association + DoWhy |

Supabase migrations: `../infra/supabase/migrations/` (repo root).

## Local dev

```bash
# From repo root
cp ../.env.example .env
# or .env.local — never commit secrets

# Web
cd trita && pnpm install && pnpm dev:web

# API (Python 3.11+)
cd trita/apps/api && pip install -e ".[dev]" && uvicorn trita_api.main:app --reload --port 8000
```

## Tests

```bash
pytest trita/apps/api/tests/test_env_example.py -q
```
