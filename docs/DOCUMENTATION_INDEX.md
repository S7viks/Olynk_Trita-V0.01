# Documentation Index — Trita V0.0.1

Single hub for humans and Cursor agents. **Authority order:** code + HANDOFF → VALIDATION → MISSION → context docs → PLAN narrative.

---

## Reading order (new agent session)

| Step | Path | Why |
|------|------|-----|
| 0 | [checklists/BASELINE.md](./checklists/BASELINE.md) | Human once; Tier A+B exists |
| — | [../HANDOFF.md](../HANDOFF.md) § RETRO 2026-05-22 | RM-1 closed; RM-2 active |
| 1 | [../MISSION.md](../MISSION.md) | Goal, milestone, active feature, Worker Procedures |
| 2 | [../VALIDATION.md](../VALIDATION.md) | VA assertions — never weaken |
| 3 | [../HANDOFF.md](../HANDOFF.md) | Latest implementation truth |
| 4 | [ROADMAP.md](./ROADMAP.md) | RM-0 … RM-5 gates |
| 5 | [BUILD-ORDER.md](./BUILD-ORDER.md) | Dependency order |
| 6 | [roadmap/phase-* for current RM](./roadmap/) | `T-P{n}-*` tasks |
| 7 | [features/REGISTRY.md](./features/REGISTRY.md) | `F-*` acceptance |
| 8 | [context/MASTER-CONTEXT.md](./context/MASTER-CONTEXT.md) | Product principles |
| 9 | [../ORCHESTRATOR.md](../ORCHESTRATOR.md) | Per-feature workflow |
| 10 | [../SCRUTINY.md](../SCRUTINY.md) | Review checklist |
| 11 | [../tests/BEHAVE.md](../tests/BEHAVE.md) | E2E command → VA map |

**Orchestrator / RETRO:** also read [../PLAN.md](../PLAN.md), [../architecture/README.md](../architecture/README.md), [CURSOR-MULTI-AGENT-WORKFLOW.md](./CURSOR-MULTI-AGENT-WORKFLOW.md).

**Feature-specific:** ADRs in [adr/](./adr/), pipelines in [pipelines/](./pipelines/), CSV hub [pipelines/P-INGEST-CSV-HUB.md](./pipelines/P-INGEST-CSV-HUB.md).

---

## Tier A — Shared state (repo root)

| File | Role |
|------|------|
| [MISSION.md](../MISSION.md) | Scope, 6 milestones ↔ RM-0…5, feature checklist |
| [VALIDATION.md](../VALIDATION.md) | VA-01 … VA-26 observable done |
| [HANDOFF.md](../HANDOFF.md) | Per-feature + Scrutiny + BEHAVE verdicts |
| [MISSION_LOG.md](../MISSION_LOG.md) | Append-only events |

---

## Tier B — Planning & architecture

| File | Role |
|------|------|
| [PLAN.md](../PLAN.md) | Product arc, phases, non-goals |
| [ROADMAP.md](./ROADMAP.md) | RM-* table, blocking VAs, ADR gates |
| [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) | This file |
| [OPEN_SOURCE_STACK.md](./OPEN_SOURCE_STACK.md) | Stack, deploy, secrets |
| [GLOSSARY.md](./GLOSSARY.md) | Shared vocabulary |
| [../architecture/README.md](../architecture/README.md) | ADR index |
| [CURSOR-MULTI-AGENT-WORKFLOW.md](./CURSOR-MULTI-AGENT-WORKFLOW.md) | Triggers, roles, paste prompts |

---

## Doc matrix (by topic)

| Topic | Primary | Supporting |
|-------|---------|------------|
| Multi-agent Cursor | [CURSOR-MULTI-AGENT-WORKFLOW.md](./CURSOR-MULTI-AGENT-WORKFLOW.md) | ORCHESTRATOR, SCRUTINY, BEHAVE |
| Product truth | [context/MASTER-CONTEXT.md](./context/MASTER-CONTEXT.md) | PLAN, TRACEABILITY |
| System design | [context/architecture.md](./context/architecture.md) | stack-oss, ADRs |
| Data model | [context/data-graph.md](./context/data-graph.md) | pipelines, dbt |
| Decisions | [context/decision-contract.md](./context/decision-contract.md) | features/decision-inbox.md |
| Causal | [context/causal-policy.md](./context/causal-policy.md) | features/causal-proactive.md |
| Connectors / CSV | [context/integrations.md](./context/integrations.md) | P-INGEST-CSV-HUB, connect-sources |
| Features | [features/REGISTRY.md](./features/REGISTRY.md) | specs under features/ |
| Pipelines | [pipelines/REGISTRY.md](./pipelines/REGISTRY.md) | P-*.md specs |
| Launch | [checklists/LAUNCH-GATE.md](./checklists/LAUNCH-GATE.md) | phase-5-launch |
| Pilot | MISSION § Pilot tenant | Yoga Bar for E2E evidence |
| **Local dev (Phase 0)** | [LOCAL-DEV.md](./LOCAL-DEV.md) | `scripts/start-local.ps1`, `scripts/dev-health.ps1` |

---

## ID conventions

See [README.md](./README.md) § ID conventions (`F-*`, `P-*`, `T-P*`, `C-*`, `VA-*`, `RM-*`).

---

## Obsolete / do not use

- `docs/BUiLD-ORDER.md` — renamed to BUILD-ORDER.md
- Connector or CSV **stubs** — forbidden per MISSION; use full raw → quarantine → dbt path
