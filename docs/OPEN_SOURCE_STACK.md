# Open Source Stack & Operations — Trita V0.0.1

Worker reference for infra, deploy, and secrets. Product stack rationale: [context/stack-oss.md](./context/stack-oss.md).  
System diagram: [context/architecture.md](./context/architecture.md).

---

## Runtime stack

| Layer | Choice | ADR / notes |
|-------|--------|-------------|
| Web | Next.js 14 (Vercel) | App Router, Supabase Auth client |
| API | FastAPI (Render) | JWT → `tenant_id` only |
| DB | Supabase Postgres + Auth + pgvector | RLS on all tenant tables |
| Ingest | dlt | Raw envelope + hash + lineage |
| Transform | dbt + dbt-expectations | Quarantine marts |
| Orchestration | **Dagster** | [ADR-001](./adr/001-orchestrator.md) Accepted |
| LLM | LiteLLM → Gemini (cards/drafts), Groq (chat) | Per-tenant budget cap |
| Metering | OpenMeter | LLM + usage events |
| Causal | DoWhy | L3 after refutation pass only |

---

## Repo layout (target)

```
trita/
├── apps/web/              # Next.js
├── apps/api/              # FastAPI
├── data/dlt/              # Ingest
├── data/dbt/              # Transform
├── data/orchestration/    # Dagster code location
├── packages/{ontology,decisions,causal}/
infra/supabase/migrations/
```

---

## Environments

| Env | Web | API | Data |
|-----|-----|-----|------|
| Local | `pnpm dev` in `trita/apps/web` | `uvicorn` + `.env.local` | Supabase local or dev project |
| Staging | Vercel preview | Render staging | Supabase staging |
| Production | Vercel prod | Render prod | Supabase prod |

Document URLs and service IDs in HANDOFF when a feature touches deploy — never commit secrets.

---

## Secrets (required in `.env.example`)

- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `DATABASE_URL` (pooler for app; direct for DDL)
- Shopify app credentials (`SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, redirect URIs)
- `YOGA_BAR_TENANT_ID`, `YOGA_BAR_SHOP_DOMAIN` (pilot dev)
- LiteLLM / provider keys; OpenMeter; `RENDER_HEALTH_URL` (VA-10)

**Rule:** `.env.example` documents names with empty or placeholder values only; real values in `.env` / `.env.local` / platform secret stores — never committed (VA-11).

---

## CI (target)

- Lint (web + api + python packages)
- **Tenant isolation** suite — blocks merge (VA-02)
- dbt parse/test on PR when `data/dbt` changes
- Dagster job smoke on orchestration changes

---

## CSV hub operations

All T1 CSV flows through **P-INGEST-CSV-HUB** — template auto-detect or column map → schema validation → `raw.csv_hub_events` → quarantine. See [pipelines/P-INGEST-CSV-HUB.md](./pipelines/P-INGEST-CSV-HUB.md).

---

## Behavioral test entrypoints

See [../tests/BEHAVE.md](../tests/BEHAVE.md). Workers must document the exact command per feature in HANDOFF for the BEHAVE agent.
