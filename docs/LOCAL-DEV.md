# Local development (default for Phase 0)

Cloud hosts (Render, Fly.io) require a payment card for paid tiers. **Phase 0 runs on your machine** against **Supabase** (cloud Postgres/Auth only — free tier available).

## Prerequisites

1. Copy env: `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`)
2. Fill `.env`: `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `YOGA_BAR_TENANT_ID` (Trita tenant UUID), `SHOPIFY_CLIENT_ID` / `SECRET` (Partner **mock app**), `SHOPIFY_DEV_SHOP_DOMAIN` (your dev store — not Yoga Bar's live Shopify)
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
| http://localhost:3000/sources → **Connect Shopify** | Preferred OAuth (session JWT → API → Shopify) |
| http://127.0.0.1:8000/dev/shopify/go?tenant_id=... | Legacy API-only OAuth (no web session) |

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

Without LiteLLM running, `/v1/llm/draft` still works but returns **budget/template fallback** (VA-07). OpenMeter / Konnect is **not** in RM-0 — see [trita/services/openmeter/README.md](../trita/services/openmeter/README.md).

Smoke test (API up; Yoga Bar `YOGA_BAR_TENANT_ID` + JWT secret in `.env`):

```powershell
python scripts/test-llm-draft.py
```

If `start-litellm.ps1` fails with `No module named 'apscheduler'`, the script now uses `python -m pip` / `python -m litellm` (same interpreter) — not bare `pip` / `litellm` on PATH.

## Data pipeline (local)

| Step | Command |
|------|---------|
| Migrations | `python scripts/apply_migrations.py` |
| Shopify sync | `python scripts/shopify_sync_only.py` (API must be up) |
| dbt | `python scripts/run_dbt.py run` |
| Dagster shell | `python scripts/run_daily_shell.py` |

## Web app (Terminal 3)

```powershell
.\scripts\start-web.ps1
```

| URL | Purpose |
|-----|---------|
| http://localhost:3000/login | Sign in (Supabase email **or** “Continue as Yoga Bar (dev)”) |
| http://localhost:3000/sources | Integration health (Shopify row from API) |

Optional in `trita/apps/web/.env.local` (or repo `.env` loaded by script):

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Dev pilot login mints JWT via `POST /dev/auth/token` using `YOGA_BAR_TENANT_ID`. Supabase users need a `memberships` row; exchange via `POST /v1/auth/exchange`.

## Port conflicts

| Port | Service |
|------|---------|
| 3000 | Next.js web |
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
| Next.js web | `.\scripts\start-web.ps1` → http://localhost:3000 (`T-P0-040`–`042`) |
