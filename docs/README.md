# Trita V0.0.1 — Documentation Hub

Ground-up build kit for **Trita by OLynk** (*Third Observer*): connected intelligence OS for Indian D2C inventory decisions.

## How to use this repo

| You are… | Start here |
|----------|------------|
| **AI worker (first run)** | [checklists/BASELINE.md](./checklists/BASELINE.md) → [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) → [../MISSION.md](../MISSION.md) → [../VALIDATION.md](../VALIDATION.md) |
| **Cursor multi-agent** | [CURSOR-MULTI-AGENT-WORKFLOW.md](./CURSOR-MULTI-AGENT-WORKFLOW.md) — `ORCHESTRATE`, `SHIP`, `SCRUTINY`, `BEHAVE`, `RETRO` |
| **New engineer** | [context/MASTER-CONTEXT.md](./context/MASTER-CONTEXT.md) → [roadmap/00-overview.md](./roadmap/00-overview.md) |
| **Implementing a feature** | [features/REGISTRY.md](./features/REGISTRY.md) → linked feature spec |
| **Building data/ETL** | [pipelines/REGISTRY.md](./pipelines/REGISTRY.md) → pipeline spec |
| **Sprint planning** | Current phase file under `roadmap/` + phase exit criteria |
| **Launch / QA** | [checklists/LAUNCH-GATE.md](./checklists/LAUNCH-GATE.md) |

## Document map

### Context (stable truth)

| File | Contents |
|------|----------|
| [MASTER-CONTEXT.md](./context/MASTER-CONTEXT.md) | Vision, ICP, in/out scope, principles |
| [architecture.md](./context/architecture.md) | System diagram, services, hosting |
| [data-graph.md](./context/data-graph.md) | Entities, edges, identity resolution |
| [decision-contract.md](./context/decision-contract.md) | Card types, fields, suppression, audit |
| [causal-policy.md](./context/causal-policy.md) | L0–L3, DoWhy gates, no simulation |
| [integrations.md](./context/integrations.md) | 10 apps, tiers, connector contract |
| [agents.md](./context/agents.md) | Fixed agent roster, boundaries |
| [stack-oss.md](./context/stack-oss.md) | OSS adopt vs build in-house |
| [product-surfaces.md](./context/product-surfaces.md) | Routes, reports, onboarding |
| [TRACEABILITY.md](./TRACEABILITY.md) | Master plan § → doc mapping |

### Roadmap (16 weeks)

| Phase | Weeks | File |
|-------|-------|------|
| 0 — Spine | 1–2 | [phase-0-spine.md](./roadmap/phase-0-spine.md) |
| 1 — Six apps + graph | 3–5 | [phase-1-six-apps-graph.md](./roadmap/phase-1-six-apps-graph.md) |
| 2 — Inventory inbox | 6–8 | [phase-2-inventory-inbox.md](./roadmap/phase-2-inventory-inbox.md) |
| 3 — Causal + proactive | 9–11 | [phase-3-causal-proactive.md](./roadmap/phase-3-causal-proactive.md) |
| 4 — Ten apps + hardening | 12–14 | [phase-4-ten-apps-hardening.md](./roadmap/phase-4-ten-apps-hardening.md) |
| 5 — Launch | 15–16 | [phase-5-launch.md](./roadmap/phase-5-launch.md) |
| Overview | — | [00-overview.md](./roadmap/00-overview.md) |

### Features & pipelines

- [features/REGISTRY.md](./features/REGISTRY.md) — All features with IDs, phase, deps, acceptance
- [pipelines/REGISTRY.md](./pipelines/REGISTRY.md) — All jobs/flows with schedules and SLAs

### Execution

- [ROADMAP.md](./ROADMAP.md) — Program milestones RM-0 … RM-5 and blocking VAs
- [BUILD-ORDER.md](./BUILD-ORDER.md) — Dependency-ordered implementation sequence
- [checklists/BASELINE.md](./checklists/BASELINE.md) — Tier A+B init trigger (human checklist)
- [checklists/LAUNCH-GATE.md](./checklists/LAUNCH-GATE.md) — Ship gate
- [checklists/phase-exit-criteria.md](./checklists/phase-exit-criteria.md) — Phase gates in one table

### Tier B (planning)

| File | Role |
|------|------|
| [../PLAN.md](../PLAN.md) | Product arc, non-goals |
| [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) | Reading order + doc matrix |
| [OPEN_SOURCE_STACK.md](./OPEN_SOURCE_STACK.md) | Stack, deploy, secrets |
| [GLOSSARY.md](./GLOSSARY.md) | Shared terms |
| [../architecture/README.md](../architecture/README.md) | ADR index |
| [CURSOR-MULTI-AGENT-WORKFLOW.md](./CURSOR-MULTI-AGENT-WORKFLOW.md) | Multi-chat workflow |

### Agent orchestration (repo root)

| File | Role |
|------|------|
| [../MISSION.md](../MISSION.md) | Mission, 6 milestones ↔ RM-0…5 |
| [../VALIDATION.md](../VALIDATION.md) | VA assertions — do not weaken after code exists |
| [../HANDOFF.md](../HANDOFF.md) | Per-feature handoff log |
| [../ORCHESTRATOR.md](../ORCHESTRATOR.md) | Worker procedures |
| [../SCRUTINY.md](../SCRUTINY.md) | Review contract |
| [../tests/BEHAVE.md](../tests/BEHAVE.md) | Behavioral test contract (stubs until `trita/`) |

## ID conventions

| Prefix | Example | Meaning |
|--------|---------|---------|
| `F-*` | `F-INBOX-003` | Product/engineering feature |
| `P-*` | `P-INGEST-SHOPIFY` | Data or orchestration pipeline |
| `T-P{n}-*` | `T-P1-012` | Phase task (in phase roadmap files) |
| `C-*` | `C-SHOPIFY` | Connector (see integrations.md) |
| `D-*` | `D-REORDER` | Decision card type |

## Repo layout (target — create incrementally)

```
trita/
├── apps/
│   ├── web/          # Next.js 14
│   └── api/          # FastAPI
├── data/
│   ├── dlt/          # Ingest taps
│   ├── dbt/          # Transform
│   └── orchestration/ # Dagster (ADR-001)
├── packages/
│   ├── ontology/     # Commerce graph + identity
│   ├── decisions/    # Contract, suppression, audit
│   └── causal/       # Association + DoWhy
├── infra/
│   └── supabase/     # Migrations, RLS
└── docs/             # This tree
```

## Rules of engagement (non-negotiable)

1. **Numbers are deterministic** — LLM never computes inventory math.
2. **No simulation** in V0.0.1 — causal association + refutation only.
3. **Tenant isolation** — CI must pass before any pilot data.
4. **Honest connector badges** — 6 production-grade at launch; 10 visible.
5. **≤7 decision cards / 7 days / tenant** — suppression is product, not optional.

## Version

- **Plan version:** V0.0.1 master (2026-05-20)
- **Product:** Trita · **Company:** OLynk
