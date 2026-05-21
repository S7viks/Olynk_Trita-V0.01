# Trita monorepo

Application code for **Trita V0.0.1** (OLynk). Planning docs live in the repo root `docs/`.

## Layout

| Path | Role |
|------|------|
| `apps/web` | Next.js 14 (Vercel) |
| `apps/api` | FastAPI (local dev; Render deferred) |
| `data/dlt` | dlt ingest taps |
| `data/dbt` | dbt transforms |
| `data/orchestration` | Dagster code location (ADR-001) |
| `packages/ontology` | Commerce graph + identity |
| `packages/decisions` | Decision contract, suppression, audit |
| `packages/causal` | Association + DoWhy |

Supabase migrations: `../infra/supabase/migrations/` (repo root).

## Local dev

**Guide:** [docs/LOCAL-DEV.md](../docs/LOCAL-DEV.md) (no Render/Fly card required).

```powershell
# From repo root (path with spaces — use quotes)
cd "d:\Olynk_V 0.0.1"
Copy-Item .env.example .env   # fill Supabase + Shopify keys
.\scripts\start-local.ps1
```

```powershell
# Health (API must be running)
.\scripts\dev-health.ps1
```

## Tests

```bash
pytest trita/apps/api/tests/test_env_example.py -q
```
