# Render deployment (T-P0-005 / VA-10)

## Services

| Service | Blueprint name | Health |
|---------|----------------|--------|
| FastAPI | `trita-api` | `GET /health` |
| LiteLLM | `trita-litellm` | `GET /health/liveliness` |

Root spec: [render.yaml](../../render.yaml) at repo root.

## First deploy

1. Push `render.yaml` to your Git remote (GitHub/GitLab).
2. Render Dashboard → **New** → **Blueprint** → connect repo → **Apply**.
3. Set secrets (`sync: false` in blueprint): `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `SHOPIFY_*`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `LITELLM_MASTER_KEY`, `NEXT_PUBLIC_WEB_URL`.
4. Set Shopify OAuth redirect to `https://<trita-api-host>/v1/sources/shopify/callback`.
5. Copy public API URL to `.env` as `RENDER_HEALTH_URL` (no trailing slash).

Validate locally (optional, requires [Render CLI](https://render.com/docs/cli)):

```bash
render blueprints validate render.yaml
```

## VA-10 check

```powershell
# After deploy — from repo root
$env:RENDER_HEALTH_URL = "https://trita-api-xxxx.onrender.com"
.\scripts\check_render_health.ps1
```

```bash
export RENDER_HEALTH_URL=https://trita-api-xxxx.onrender.com
./scripts/check_render_health.sh
```

Expect exit **0** and JSON `{"status":"ok",...}`.

7-day stability is an ops cadence (re-run weekly); CI uses blueprint contract tests only.

## Local API (pre-Render)

```powershell
.\scripts\start-api.ps1
curl -sf http://127.0.0.1:8000/health
```
