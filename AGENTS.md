# AGENTS.md — Trita V0.0.1

Instructions for AI coding agents working in this repository.

---

## Project

**Trita** by **OLynk** — Third Observer inventory intelligence for Indian D2C (₹5–50 Cr). Web-first V0.0.1: graph + Decision Inbox + causal discipline (no simulation).

---

## Multi-agent Cursor workflow

Triggers and paste prompts: [docs/CURSOR-MULTI-AGENT-WORKFLOW.md](docs/CURSOR-MULTI-AGENT-WORKFLOW.md).  
Doc hub: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md).

| Trigger | Role |
|---------|------|
| `BASELINE` | Human checklist — Tier A+B |
| `ORCHESTRATE` | Planning only |
| `SHIP` | One feature (Worker) |
| `SCRUTINY` / `PATCH` | Review / fix |
| `BEHAVE` | Automated E2E vs VAs |
| `RETRO` / `NOGO` / `DOCFIX` | Milestone / recovery |
| `REANCHOR` | Drift recovery |

## After BASELINE

Human trigger: [docs/checklists/BASELINE.md](docs/checklists/BASELINE.md) (`BASELINE` — checklist only, no dedicated AI chat).

Worker read order:

1. [MISSION.md](MISSION.md) — goal, milestone, feature priority
2. [VALIDATION.md](VALIDATION.md) — VA assertions for done
3. [ORCHESTRATOR.md](ORCHESTRATOR.md) — handoff and routing
4. [SCRUTINY.md](SCRUTINY.md) — separate reviewer contract
5. [docs/CURSOR-MULTI-AGENT-WORKFLOW.md](docs/CURSOR-MULTI-AGENT-WORKFLOW.md) — when starting a new chat role

---

## Read first

1. [docs/context/MASTER-CONTEXT.md](docs/context/MASTER-CONTEXT.md) — scope and principles
2. [docs/BUILD-ORDER.md](docs/BUILD-ORDER.md) — what to implement next
3. [docs/ROADMAP.md](docs/ROADMAP.md) — RM-0 … RM-5 program gates
4. Current phase: [docs/roadmap/](docs/roadmap/) — task IDs `T-P{n}-*`

---

## Non-negotiable rules

1. **Deterministic engine owns all inventory numbers.** LLM must not compute qty, cover, ₹ impact.
2. **No simulation / digital twin** in V0.0.1.
3. **`tenant_id` from JWT only** — never trust request body; RLS + app filter.
4. **Decision suppression:** dedup `(tenant, type, sku, week)`; max 7 new cards / 7 days.
5. **Integrity suppress:** if Shopify or Unicommerce stale past SLA, do not emit inventory decisions.
6. **Causal labels L0–L3** per [docs/context/causal-policy.md](docs/context/causal-policy.md); L3 only after DoWhy refutation pass.
7. **Tier 3 execution disabled** — no auto-write to external systems.
8. **6 production connectors at launch; 10 honest badges** in UI.

---

## Stack (target)

- **web:** Next.js 14 (Vercel)
- **api:** FastAPI (Render)
- **db:** Supabase Postgres + Auth + pgvector
- **ingest:** dlt
- **transform:** dbt + dbt-expectations
- **orchestration:** Dagster (ADR-001 Accepted)
- **llm:** LiteLLM → Gemini (cards/drafts), Groq (chat)
- **metering:** OpenMeter
- **causal:** DoWhy

---

## Key packages (when scaffolded)

| Path | Responsibility |
|------|----------------|
| `packages/ontology/` | Identity resolution, SKU aliases |
| `packages/decisions/` | Card contract, suppression, audit |
| `packages/causal/` | Association, DoWhy, promotion policy |

---

## Before merging

- [ ] Tenant isolation tests pass
- [ ] Feature ID noted in PR description (`F-*`)
- [ ] Update [docs/features/REGISTRY.md](docs/features/REGISTRY.md) status if applicable
- [ ] No secrets in git

---

## Supabase

Use Supabase MCP / CLI for schema changes; migrations in `infra/supabase/migrations/`. Review RLS on every new table.

---

## Commercial context

Launch gate: [docs/checklists/LAUNCH-GATE.md](docs/checklists/LAUNCH-GATE.md) via **VA-20**. Pilot tenant for build evidence: **Yoga Bar**.
