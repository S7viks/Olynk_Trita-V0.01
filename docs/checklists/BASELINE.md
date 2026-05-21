# BASELINE Checklist

**Trigger:** `BASELINE` — human or orchestrator notebook step only. **No dedicated AI chat** for this checklist.

Run once before the first implementation worker agents touch code.

---

## Tier A (repo root)

- [ ] [`MISSION.md`](../../MISSION.md) exists and names **Trita V0.0.1**
- [ ] [`VALIDATION.md`](../../VALIDATION.md) exists; VA-01+ defined; bar not weakened
- [ ] [`HANDOFF.md`](../../HANDOFF.md) exists with bootstrap entry
- [ ] [`MISSION_LOG.md`](../../MISSION_LOG.md) exists with mission-started row

---

## Tier B (extended — non-toy scope)

- [ ] [`PLAN.md`](../../PLAN.md) — product arc
- [ ] [`docs/ROADMAP.md`](../ROADMAP.md) — RM-0 … RM-5 with blocking VAs
- [ ] [`docs/DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md) — reading order
- [ ] [`docs/CURSOR-MULTI-AGENT-WORKFLOW.md`](../CURSOR-MULTI-AGENT-WORKFLOW.md) — triggers + prompts
- [ ] [`docs/OPEN_SOURCE_STACK.md`](../OPEN_SOURCE_STACK.md) — stack / deploy
- [ ] [`docs/GLOSSARY.md`](../GLOSSARY.md) — vocabulary
- [x] [`architecture/README.md`](../../architecture/README.md) — ADR index (ADR-001 Dagster Accepted)
- [ ] [`ORCHESTRATOR.md`](../../ORCHESTRATOR.md) — worker read order and handoff rules
- [ ] [`SCRUTINY.md`](../../SCRUTINY.md) — review contract
- [ ] [`tests/BEHAVE.md`](../../tests/BEHAVE.md) — behavioral contract stub

---

## Wiring

- [ ] [`AGENTS.md`](../../AGENTS.md) points to MISSION → VALIDATION → workflow doc
- [ ] [`docs/BUILD-ORDER.md`](../BUILD-ORDER.md) path resolves (not `BUiLD-ORDER`)
- [ ] [`README.md`](../../README.md) status reflects baseline initialized

---

## Log

- [ ] Append row to `MISSION_LOG.md`: `BASELINE Tier A+B verified`

---

## After BASELINE

Proceed to **Layer 0** item 1 in [BUILD-ORDER.md](../BUILD-ORDER.md) (monorepo scaffold `trita/`). Workers must read [`MISSION.md`](../../MISSION.md) and mapped VAs before coding.
