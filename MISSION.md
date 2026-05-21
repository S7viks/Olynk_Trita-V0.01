# Mission: Trita V0.0.1

## Goal

**Trita** by **OLynk** is a web-first *Third Observer* for Indian D2C brands (₹5–50 Cr revenue). It connects the tools merchants already use into one tenant-scoped graph, surfaces proactive **inventory decisions** in a Decision Inbox with ₹-backed evidence and approve/reject audit, and explains drivers with causal discipline (L0–L3) — without simulation or autonomous external writes in V0.0.1.

## Pilot tenant

**Yoga Bar** is the primary tenant for E2E ingest, milestone review evidence, and launch readiness (replaces generic “test tenant” in validation assertions).

## Tech Stack

- **Language/Framework:** Next.js 14 (web), FastAPI (API), Python packages (`ontology`, `decisions`, `causal`)
- **Database:** Supabase Postgres + Auth + pgvector; RLS on all tenant data
- **Auth:** Supabase Auth; `tenant_id` from JWT only
- **Deployment target:** Vercel (web), Render (API), Supabase (data)
- **Key libraries:** dlt, dbt + dbt-expectations, **Dagster** (ADR-001 Accepted), LiteLLM (Gemini/Groq), OpenMeter, DoWhy

## Features (ordered by priority)

### Milestone 1 — RM-0: Phase 0 spine (Weeks 1–2)

1. [x] Monorepo scaffold `trita/` — [docs/BUILD-ORDER.md](docs/BUILD-ORDER.md) item 1
2. [x] Supabase `tenants`, `memberships` + RLS — `F-PLAT-001`, `T-P0-001`
3. [x] Tenant isolation CI — `F-PLAT-002`, `T-P0-002` _(RLS contract + GitHub workflow; `T-P0-003` service_role audit next)_
4. [x] `.env.example` (no secrets) — BUILD-ORDER item 4
5. [x] ADR-001 **Dagster** — status **Accepted** — `T-P0-050`
6. [x] FastAPI + JWT middleware — `T-P0-004`
7. [x] Render deploy stable — `T-P0-005` _(blueprint + health; apply Blueprint for live URL)_
8. [x] dlt raw envelope + Shopify tap — `F-INGEST-SHOPIFY`, `T-P0-010`–`T-P0-011`
9. [x] Shopify **OAuth** + API sync — `T-P0-011`, `T-P0-013` _(webhooks/HMAC `T-P0-012` deferred; **VA-04** deferred)_
10. [x] dbt staging + gold shell — `F-GRAPH-SHELL`, `T-P0-020`–`T-P0-021`
11. [ ] LiteLLM + OpenMeter — `F-PLAT-003` **done**, `F-PLAT-004` planned, `T-P0-030`–`T-P0-032` _(OpenMeter T-P0-032 pending)_
12. [ ] Next auth + Sources shell — `F-UI-NAV`, `F-UI-SOURCES-SHELL`, `T-P0-040`–`T-P0-042`
13. [ ] Integration health API — `F-CONN-HEALTH`
14. [x] Dagster job: ingest → dbt — `P-ORCH-DAILY-SHELL`, `T-P0-051`
15. [ ] **Gate (RM-0):** Yoga Bar — Shopify → raw → gold; health row visible; **no** decision cards

### Milestone 2 — RM-1: Six apps + graph (Weeks 3–5)

16. [ ] Connectors 2–4, 6 (API/scheduled) — `F-CONN-002`, `003`, `004`, `006`
17. [ ] **CSV hub (production)** — `F-CONN-005`: template auto-detect **or** column map → schema validation → raw envelope → quarantine → gold ([P-INGEST-CSV-HUB](docs/pipelines/P-INGEST-CSV-HUB.md)); Tally/Amazon CSV routes through hub
18. [ ] Identity v1 — `F-ID-001`, `F-ID-002`
19. [ ] Gold models + metrics pipelines — `F-METRICS-001`..`004`
20. [ ] Data Health report + inventory list UI — `F-REPORT-HEALTH`, `F-UI-INVENTORY-LIST`, `F-UI-SOURCES`
21. [ ] **Gate (RM-1):** Yoga Bar — ≥90% order lines resolved; Data Health matches gold; CSV upload path proven (VA-26)

### Milestone 3 — RM-2: Inventory inbox (Weeks 6–8)

22. [ ] Decision contract + emitter + suppression — `F-DEC-001`..`004`
23. [ ] Audit API + Inbox UI — `F-DEC-005`, `F-INBOX-001`..`004`
24. [ ] Tier-2 drafts on approve — `F-DRAFT-001`, `F-DRAFT-002`
25. [ ] **Gate (RM-2):** Yoga Bar — accept/reject ≥1 card with reason enum

### Milestone 4 — RM-3: Causal + proactive (Weeks 9–11)

26. [ ] Causal association + DoWhy + card copy — `F-CAUSAL-001`..`003`
27. [ ] Proactive triggers, digest, chat — `F-PROACTIVE-001`..`004`, `F-CHAT-001`, `F-CHAT-002`
28. [ ] Connectors 7–9 — `F-CONN-007`..`009`
29. [ ] **Gate (RM-3):** Yoga Bar — ≥1 card with L2 or L3 driver + evidence refs

### Milestone 5 — RM-4: Ten apps + hardening (Weeks 12–14)

30. [ ] GA4 + Amazon connectors — `F-GA4`, `F-CONN-010` (Amazon CSV via hub)
31. [ ] Security hardening — `F-SEC-001`, `F-SEC-002`; load test — per phase-4 doc
32. [ ] **Gate (RM-4):** 10 honest Sources badges; red team + load evidence in `docs/ops/`

### Milestone 6 — RM-5: Launch (Weeks 15–16)

33. [ ] **Gate (RM-5):** [LAUNCH-GATE.md](docs/checklists/LAUNCH-GATE.md) complete (VA-20); product ready to ship
34. [ ] First paying customer @ ₹10K+ MRR (commercial evidence; not a separate VA)

## Milestones (1:1 with program roadmap)

| Milestone | RM | Features | Exit |
|-----------|-----|----------|------|
| **1** | RM-0 | 1–15 | Yoga Bar Shopify E2E; no inbox |
| **2** | RM-1 | 16–21 | Six connectors + CSV hub E2E; graph + health accurate |
| **3** | RM-2 | 22–25 | Inbox + pilot accept/reject |
| **4** | RM-3 | 26–29 | Causal L2/L3 on a card |
| **5** | RM-4 | 30–32 | 10 sources UI; hardening docs |
| **6** | RM-5 | 33–34 | Launch checklist; paying customer |

Granular tasks: [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/roadmap/`](docs/roadmap/).

## Out of Scope

- **Connector or ingest stubs** — no upload/UI that skips raw → validate → quarantine → dbt
- Simulation / digital twin / L5 kernel
- RL / auto policy training
- Mobile app, WhatsApp-first
- Tier-3 auto-write to Shopify, Unicommerce, or other external systems
- Full logistics/finance product modules (data in graph; dedicated UI later)
- 25 connectors day one; cross-tenant benchmarks
- Auto-spawn agents per tenant

## Constraints & Decisions

- Deterministic engine owns all inventory numbers; LLM owns language only
- Decision suppression: dedup `(tenant, type, sku, week)`; max 7 new cards / 7 days
- Integrity suppress when Shopify or Unicommerce stale past SLA
- Causal L0–L3 per [docs/context/causal-policy.md](docs/context/causal-policy.md)
- 6 production-grade connectors at launch; 10 honest badges in UI
- CSV hub: any layout via template detect or column map; shared schema validation and data lifecycle ([P-INGEST-CSV-HUB](docs/pipelines/P-INGEST-CSV-HUB.md))
- **Orchestrator:** Dagster — [docs/adr/001-orchestrator.md](docs/adr/001-orchestrator.md) (**Accepted**)
- Architecture: [docs/context/architecture.md](docs/context/architecture.md)

## Worker Procedures

**Read order:** `MISSION.md` → `VALIDATION.md` (mapped VAs) → `docs/ROADMAP.md` (RM gate) → `docs/roadmap/phase-*.md` → `docs/features/REGISTRY.md` → `docs/BUILD-ORDER.md`.

**Repo layout (when scaffolded):**

| Path | Role |
|------|------|
| `trita/apps/web` | Next.js 14 |
| `trita/apps/api` | FastAPI |
| `trita/packages/{ontology,decisions,causal}` | Domain logic; no LLM inventory math |
| `trita/data/{dlt,dbt}` | Ingest + transform |
| `infra/supabase/migrations/` | Schema + RLS (review RLS on every new table) |

**Naming:** Feature `F-*`, pipeline `P-*`, task `T-P{n}-*`, assertion `VA-*`. Update `docs/features/REGISTRY.md` status when shipping.

**Forbidden:** `tenant_id` from request body; LLM reorder qty / cover / ₹ impact; Tier-3 external writes; weakening `VALIDATION.md`; simulation in prod config; connector/CSV **stubs** (upload without validate → raw → quarantine).

**ADRs:** `docs/adr/` — update Status in-file. RM-0 requires ADR-001 **Accepted** (Dagster).

**Contract changes:** Decision/card JSON → feature spec + `packages/decisions/`; engine metrics → `packages/ontology/` or dbt docs; Dagster graph → `docs/pipelines/REGISTRY.md` + ADR if scheduler semantics change.

**Handoff:** Append `HANDOFF.md`; separate scrutiny per `SCRUTINY.md`; log `MISSION_LOG.md`. Full workflow: [`ORCHESTRATOR.md`](ORCHESTRATOR.md).

## Status

Current Milestone: 1 (RM-0)
Active Feature: Next auth + Sources shell — `T-P0-040`–`T-P0-042` or OpenMeter `F-PLAT-004`
Pilot tenant: Yoga Bar
Last Updated: 2026-05-20 (Render blueprint T-P0-005, LiteLLM F-PLAT-003)
