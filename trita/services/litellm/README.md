# LiteLLM proxy (F-PLAT-003 / T-P0-030)

Gemini (`gemini-cards`) for card/draft copy; Groq (`groq-chat`) for chat (RM-2+).

## Local

```powershell
# From repo root — load GEMINI_API_KEY, GROQ_API_KEY, LITELLM_MASTER_KEY in .env
.\scripts\start-litellm.ps1
# Proxy: http://127.0.0.1:4000
```

**Windows:** bare `litellm --config` often fails (`apscheduler`, `fastapi_sso`, or `uvloop`). `start-litellm.ps1` uses `scripts/run_litellm_proxy.py` (asyncio loop + `config.yaml`). If port 4000 is stuck, stop the old process and restart.

Smoke test (API in terminal 2):

```powershell
python scripts/test-llm-draft.py
```

Set in `.env`:

```
LITELLM_PROXY_URL=http://127.0.0.1:4000
LITELLM_MASTER_KEY=<random>
```

## Render

Deployed as `trita-litellm` in [render.yaml](../../../render.yaml). API receives `LITELLM_PROXY_URL` via `fromService`.

## Budget (T-P0-031 / VA-07)

FastAPI enforces per-tenant token budget (`LITELLM_TENANT_TOKEN_BUDGET`, default 5000). Over cap → template fallback, no upstream completion.
