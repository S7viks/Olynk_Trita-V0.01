# Trita API

FastAPI service (Render). **`tenant_id` from JWT only** (`T-P0-004`, VA-01).

JWT claims: `sub` (user), `tenant_id`, `role`. Set `API_JWT_SECRET` to the Supabase project JWT secret.

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /health` | No | Liveness (Render VA-10) |
| `POST /v1/llm/draft` | Yes | Narrative draft via LiteLLM; budget fallback (VA-07) |
| `GET /v1/llm/budget` | Yes | Tenant token usage vs cap |
| `GET /v1/tenant/context` | Bearer | Current tenant from token |
| `POST /v1/tenant/probe` | Bearer | Rejects body `tenant_id` override |
| `GET /v1/sources/shopify/connect` | Bearer | Start Shopify OAuth |
| `GET /v1/sources/shopify/callback` | Public | OAuth callback (state JWT) |
| `POST /v1/sources/shopify/sync` | Bearer | Admin API → `raw.shopify_events` |
| `GET /v1/sources/shopify/status` | Bearer | Connected shop (no token in response) |

```bash
pip install -e ".[dev]"
uvicorn trita_api.main:app --reload --port 8000
pytest tests/test_tenant_from_jwt.py tests/isolation/ -q
```
