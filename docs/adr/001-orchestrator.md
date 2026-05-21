# ADR 001: Workflow Orchestrator

**Status:** Accepted  
**Date:** 2026-05-20  
**Accepted for:** T-P0-050 (BUILD-ORDER item 5)  
**Context:** Ingest → dbt → metrics → decisions → causal must run reliably with idempotency.

---

## Decision

**Dagster** — asset lineage, first-class dbt integration, per-tenant partitions for pilot tenants (e.g. Yoga Bar).

Prefect was not selected; simpler deploy was outweighed by dbt/asset model needs for V0.0.1.

---

## Options (record)

| Option | Pros | Cons |
|--------|------|------|
| **Dagster** (chosen) | Asset lineage, data-aware scheduling, good dbt integration | Heavier ops |
| **Prefect** | Simpler deploy, Python-native | Asset model less central |

---

## Criteria (met)

1. dbt invocation as first-class
2. Per-tenant partition or config map for pilots
3. Idempotent run keys
4. Render-compatible worker deploy
5. Team familiarity

---

## Consequences

- All pipelines in [pipelines/REGISTRY.md](../pipelines/REGISTRY.md) implemented as Dagster jobs/assets
- Single `P-ORCH-DAILY` meta-job chains ingest → dbt dependencies
- No cron scattered in Render without a Dagster schedule/sensor record
- Phase 0 job `P-ORCH-DAILY-SHELL` (`T-P0-051`) is the first Dagster deployment proof (VA-09)

---

## Acceptance record (T-P0-050)

| Criterion | Met |
|-----------|-----|
| Decision documented with options and consequences | Yes |
| Linked from `architecture/README.md` ADR index | Yes |
| `docs/pipelines/REGISTRY.md` names Dagster as orchestrator | Yes |
| Code location path `trita/data/orchestration/` reserved | Yes |
| Runtime job proof | **T-P0-051** done — `daily_shell_job` ([P-ORCH-DAILY-SHELL.md](../pipelines/P-ORCH-DAILY-SHELL.md), `scripts/run_daily_shell.py`) |

Workers must not add Render/cron ingest→dbt paths outside Dagster without a new ADR.

---

## Supersedes

Prior **Proposed** / TBD state (2026-05-20 planning).
