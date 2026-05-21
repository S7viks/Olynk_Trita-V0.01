# Architecture — ADR Index (Trita V0.0.1)

Architecture narrative: [docs/context/architecture.md](../docs/context/architecture.md).  
This folder holds **Architecture Decision Records** only.

---

## Status legend

| Status | Meaning |
|--------|---------|
| **Accepted** | Workers must follow; change only via superseding ADR |
| **Proposed** | Under discussion — do not treat as locked |
| **Superseded** | Replaced — follow link to successor |

---

## ADRs

| ID | Title | Status | Path |
|----|-------|--------|------|
| **ADR-001** | Workflow orchestrator (**Dagster**) | **Accepted** | [docs/adr/001-orchestrator.md](../docs/adr/001-orchestrator.md) |

---

## When to add an ADR

- Scheduler semantics change (Dagster assets/jobs)
- Engine or decision JSON contract changes
- Auth/tenant model changes
- New external write tier (Tier 3 must stay disabled in V0.0.1)

**Process:** Copy template below → numbered file in `docs/adr/` → link here → reference in MISSION/VALIDATION gates if milestone-blocking.

---

## ADR template

```markdown
# ADR NNN: [Title]

**Status:** Proposed
**Date:** YYYY-MM-DD
**Context:** [Problem]
**Decision:** [Choice]
**Consequences:** [What workers must do]
```

---

## Related

- [docs/OPEN_SOURCE_STACK.md](../docs/OPEN_SOURCE_STACK.md)
- [MISSION.md](../MISSION.md) § Constraints
- [VALIDATION.md](../VALIDATION.md) — VA-09 (Dagster), RM-0 gate
