# Local development (default for Phase 0)

Cloud hosts (Render, Fly.io) require a payment card for paid tiers. **Phase 0 runs on your machine** against **Supabase** (cloud Postgres/Auth only — free tier available).

## Prerequisites

1. Copy env: `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`)
2. Fill `.env`: `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `YOGA_BAR_TENANT_ID`, Shopify keys (see [infra/supabase/PROJECT.md](../infra/supabase/PROJECT.md))
3. Python 3.11+ and pip

## One-terminal API (minimum)

```powershell
cd "d:\Olynk_V 0.0.1"
.\scripts\start-api.ps1
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/health | Liveness |
| http://127.0.0.1:8000/docs | OpenAPI |
| http://127.0.0.1:8000/dev/shopify/go?tenant_id=...&shop=tritabyolynk | Shopify OAuth (dev) |

Set in `.env`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
RENDER_HEALTH_URL=http://127.0.0.1:8000
ENVIRONMENT=development
```

Health check:

```powershell
.\scripts\check_render_health.ps1
# Uses RENDER_HEALTH_URL — works locally when set to 127.0.0.1:8000
```

## Two-terminal stack (API + LiteLLM)

**Terminal 1 — LiteLLM** (optional; needed for live LLM drafts, not for ingest/dbt):

```powershell
.\scripts\start-litellm.ps1
```

**Terminal 2 — API:**

```powershell
.\scripts\start-api.ps1
```

`.env`:

```
LITELLM_PROXY_URL=http://127.0.0.1:4000
LITELLM_MASTER_KEY=<any random string for local proxy>
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

Without LiteLLM running, `/v1/llm/draft` still works but returns **budget/template fallback** (VA-07).

## Data pipeline (local)

| Step | Command |
|------|---------|
| Migrations | `python scripts/apply_migrations.py` |
| Shopify sync | `python scripts/shopify_sync_only.py` (API must be up) |
| dbt | `python scripts/run_dbt.py run` |
| Dagster shell | `python scripts/run_daily_shell.py` |

## Port conflicts

| Port | Service |
|------|---------|
| 8000 | FastAPI (`TRITA_API_PORT` to override) |
| 4000 | LiteLLM (`LITELLM_PORT` to override) |

If 8000 is busy, `start-api.ps1` exits with instructions. Update `SHOPIFY_REDIRECT_URI` / `NEXT_PUBLIC_API_URL` if you change the API port.

## Cloud deploy (deferred)

- [render.yaml](../render.yaml) and [infra/render/README.md](../infra/render/README.md) remain for when you add billing.
- **VA-10 (live)** is N/A until a public URL exists; **local** health via `RENDER_HEALTH_URL=http://127.0.0.1:8000` satisfies day-to-day dev.

## What stays in the cloud

| Service | Local? |
|---------|--------|
| Postgres + Auth | Supabase (remote) — required |
| FastAPI | Local |
| LiteLLM | Local |
| dbt / Dagster | Local CLI |
| Next.js web | Not scaffolded yet (`T-P0-040`) |
