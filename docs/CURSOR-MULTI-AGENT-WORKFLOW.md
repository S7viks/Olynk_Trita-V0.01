# Cursor Multi-Agent Workflow — Trita V0.0.1

Missions-inspired system for solo builders. Run in **separate Cursor chats** per role; **files on disk** are shared state.

**Project:** Trita by OLynk · repo root `d:\Olynk_V 0.0.1` (or workspace root).  
**Pilot tenant:** Yoga Bar · **Orchestrator:** Dagster (ADR-001 Accepted).

---

## Trita crosswalk (use these `@` paths)


| Workflow artifact         | Location                              |
| ------------------------- | ------------------------------------- |
| Mission + procedures      | `@MISSION.md`                         |
| Validation (VAs)          | `@VALIDATION.md`                      |
| Handoff + scrutiny/BEHAVE | `@HANDOFF.md`                         |
| Log                       | `@MISSION_LOG.md`                     |
| Product arc               | `@PLAN.md`                            |
| RM-* gates                | `@docs/ROADMAP.md`                    |
| Doc hub / reading order   | `@docs/DOCUMENTATION_INDEX.md`        |
| Stack / deploy            | `@docs/OPEN_SOURCE_STACK.md`          |
| Glossary                  | `@docs/GLOSSARY.md`                   |
| ADR index                 | `@architecture/README.md`             |
| ADR-001 Dagster           | `@docs/adr/001-orchestrator.md`       |
| Worker routing (extended) | `@ORCHESTRATOR.md`                    |
| Scrutiny checklist        | `@SCRUTINY.md`                        |
| Behavioral suites         | `@tests/BEHAVE.md`                    |
| Build sequence            | `@docs/BUILD-ORDER.md`                |
| Features                  | `@docs/features/REGISTRY.md`          |
| CSV hub pipeline          | `@docs/pipelines/P-INGEST-CSV-HUB.md` |
| Product truth             | `@docs/context/MASTER-CONTEXT.md`     |
| BASELINE (human)          | `@docs/checklists/BASELINE.md`        |


There is **no** `sim-studio/` prefix — all paths are from this repo root.

---

## How this works

Four+ roles across chats. Each reads **Tier A** at minimum; Orchestrator and RETRO also read **Tier B**.

### Tier A — Minimal (always)

```
MISSION.md
VALIDATION.md
HANDOFF.md
MISSION_LOG.md
```

### Tier B — Planning & architecture (this repo)

```
PLAN.md
docs/ROADMAP.md
docs/DOCUMENTATION_INDEX.md
docs/OPEN_SOURCE_STACK.md
architecture/README.md
docs/GLOSSARY.md
docs/CURSOR-MULTI-AGENT-WORKFLOW.md   ← this file
```

**Rule:** Workers read ADR / STACK slices when touching orchestration, deploy, or engine contracts. HANDOFF is session truth; chats are disposable.

---

## Model selection per role


| Role                       | Model                              | Why                       |
| -------------------------- | ---------------------------------- | ------------------------- |
| Orchestrator               | Slow / reasoning                   | Planning depth            |
| Worker                     | Fast / code                        | Feature iteration         |
| Scrutiny                   | **Different provider** than Worker | Reduce shared bias        |
| Behavioral (BEHAVE)        | Command-capable, detail-oriented   | Run pytest/curl suites    |
| Milestone Reviewer (RETRO) | Reasoning                          | Debt + doc sweep          |
| NO-GO / REANCHOR           | Reasoning                          | Classification + recovery |


Set model in Cursor **before** pasting the prompt.

---

## Trigger words

**Always paste the full PROMPT block** (ROLE LOCK inside). Line-one trigger is optional routing for you.


| Phase | Role               | Trigger       | When                                                       |
| ----- | ------------------ | ------------- | ---------------------------------------------------------- |
| 0     | You                | `BASELINE`    | Once — [BASELINE.md](./checklists/BASELINE.md), no AI chat |
| 1     | Orchestrator       | `ORCHESTRATE` | Planning / re-scope                                        |
| 2     | Worker             | `SHIP`        | One feature                                                |
| 3     | Scrutiny           | `SCRUTINY`    | After Worker                                               |
| 3b    | Fix Worker         | `PATCH`       | Scrutiny FAIL only                                         |
| 4     | Behavioral         | `BEHAVE`      | Automated E2E per HANDOFF                                  |
| 5     | Milestone Reviewer | `RETRO`       | End of RM / MISSION milestone                              |
| 5b    | NO-GO Recovery     | `NOGO`        | After RETRO NO-GO                                          |
| —     | Doc drift          | `DOCFIX`      | Situation 3                                                |
| 6     | Re-Anchor          | `REANCHOR`    | Drift / broken assertions                                  |


**Example:**

```text
SHIP

[paste PROMPT — Worker below]
```

---

## Phase 0: Setup (you, once)

Trigger `BASELINE` checklist. Tier A exists; Tier B includes files listed above.

---

## Phase 1: Orchestrator — `ORCHESTRATE`

Reasoning model · fresh chat · planning only unless user expands scope.

### PROMPT — Orchestrator

```
ROLE LOCK
- Activation token: ORCHESTRATE (case-insensitive). Line 1 ORCHESTRATE ⇒ Orchestrator until revoked.
- Message ONLY `ORCHESTRATE`: confirm role, list @MISSION.md @VALIDATION.md @PLAN.md @docs/DOCUMENTATION_INDEX.md @docs/ROADMAP.md @architecture/README.md, ask to proceed.

You are Orchestrator for Trita V0.0.1. Planning and scoping only.

Read (skip missing Tier B):
- @MISSION.md
- @VALIDATION.md
- @PLAN.md
- @docs/DOCUMENTATION_INDEX.md
- @docs/ROADMAP.md
- @architecture/README.md

Then:
1. CLARIFY — up to 5 questions; wait for answers.
2. Propose MISSION.md edits (do not apply until approved).
3. Extend VALIDATION.md — observable VAs; map features; never "internals work."
4. ROADMAP alignment — 6 MISSION milestones ↔ RM-0…RM-5; ADR-001 Dagster; VA gates.
5. Worker Procedures in MISSION (or confirm existing block).
6. Wait for explicit "approved" → apply MISSION + VALIDATION + MISSION_LOG planning row.

Trita constraints to preserve: tenant_id from JWT only; no LLM inventory math; no simulation; no connector/CSV stubs; CSV hub full lifecycle (P-INGEST-CSV-HUB); Yoga Bar pilot; launch commercial via VA-20 + LAUNCH-GATE only.
```

---

## Phase 2: Worker — `SHIP`

Fast model · **fresh chat per feature**.

### PROMPT — Worker

```
ROLE LOCK
- Activation token: SHIP. Line 1 SHIP ⇒ Worker until revoked.
- ONLY `SHIP`: acknowledge; ask for Assigned feature + Assertions from @MISSION.md / @VALIDATION.md.

You are a Worker for Trita V0.0.1 — single feature only.

Read in order:
1. @MISSION.md — goal, Worker Procedures, forbidden edits
2. @VALIDATION.md — mapped VAs for this feature
3. @HANDOFF.md — full history
4. @docs/ROADMAP.md — which RM-* this advances
5. @docs/BUILD-ORDER.md — dependencies
6. @docs/features/REGISTRY.md — acceptance for F-*
7. @docs/roadmap/phase-*.md — T-P* tasks if applicable
8. @docs/adr/001-orchestrator.md if touching Dagster/pipelines
9. @docs/pipelines/P-INGEST-CSV-HUB.md if touching CSV hub or Tally/Amazon CSV
10. @docs/OPEN_SOURCE_STACK.md if touching deploy/infra
11. @ORCHESTRATOR.md — handoff + integrity abort rules

Assigned feature: [PASTE FROM MISSION.md]
Assertions: [PASTE VA IDs FROM VALIDATION.md]

Rules:
- No tenant_id from request body; no LLM qty/cover/₹; no Tier-3 external writes
- No connector/CSV stubs — upload must validate → raw → quarantine → dbt
- Touch only files needed; scope creep → HANDOFF, stop
- Add/update tests mapped to VAs; document BEHAVE command in HANDOFF
- Pilot evidence tenant: Yoga Bar where E2E applies

When done:
1. Run tests; HANDOFF with commands + exit codes
2. Commit: feat: [feature] — VA-XX (if user asked to commit)
3. Update MISSION checkboxes / Active Feature / Last Updated
4. MISSION_LOG one line
5. Say "Ready for validation" + VA list

Start with short plan; wait for go-ahead if user wants gating.
```

---

## Phase 3: Scrutiny — `SCRUTINY`

Different provider · fresh chat · also follow @SCRUTINY.md.

### PROMPT — Scrutiny Validator

```
ROLE LOCK
- Activation token: SCRUTINY. Adversarial review only — no feature implementation.

Read: @VALIDATION.md, @HANDOFF.md (latest entry), @MISSION.md, @SCRUTINY.md, relevant ADRs.

Assertions: [PASTE LIST]

Checks:
1. Types (tsc/mypy/pyright per stack)
2. Lint — errors
3. Tests — full relevant suite
4. Code review — tenancy, deterministic engine, decisions/causal if touched, no stubs
5. Per-assertion PASS/FAIL/PARTIAL
6. VERDICT PASS/FAIL

Append HANDOFF: "## Scrutiny Validation — [date] — [PASS/FAIL]"
```

---

### PROMPT — Fix Worker — `PATCH`

```
ROLE LOCK
- Activation token: PATCH. Fix ONLY Scrutiny FAIL bullets in HANDOFF.

Read FAILURE section; minimal diff; tests green; commit fix: ...; "Ready for re-validation".
```

---

## Phase 4: Behavioral — `BEHAVE`

Fresh chat · run commands from @tests/BEHAVE.md and HANDOFF — **no manual click scripts**.

### PROMPT — Behavioral Validator

```
ROLE LOCK
- Activation token: BEHAVE. Run automated tests only; map exit codes/JUnit to VAs.

Read: @VALIDATION.md, @HANDOFF.md (Scrutiny must be PASS), @tests/BEHAVE.md, @README.md.

Assigned assertions: [PASTE VA IDs]

1. Environment check (API_URL, TEST_JWT, Yoga Bar seed if needed)
2. Run suites HANDOFF documents (pytest, curl wrappers, dagster job execute, etc.)
3. Map each VA PASS/FAIL — FAIL if no automated test mapped
4. Append HANDOFF "## Behavioral (automated) — [date] — PASS/FAIL" with commands

Do not mark MISSION done on FAIL.
```

---

## Phase 5: Milestone Review — `RETRO`

After MISSION milestone / RM-* close attempt.

### PROMPT — Milestone Reviewer

```
ROLE LOCK
- Activation token: RETRO. Milestone [N] ↔ RM-[N-1] or per MISSION table.

Read: @MISSION.md @VALIDATION.md @HANDOFF.md @MISSION_LOG.md @PLAN.md @docs/ROADMAP.md @docs/DOCUMENTATION_INDEX.md @README.md @architecture/README.md @docs/GLOSSARY.md @docs/OPEN_SOURCE_STACK.md if infra touched.

Produce:
1. Completion check (features + Scrutiny + BEHAVE)
2. Assertion coverage — honest [x] in VALIDATION only when proven
3. Debt log
4. Follow-ups for next milestone
5. Risk flags
6. Git audit vs LOG
7. GO / NO-GO — RM gates, ADR-001, doc drift

NO-GO → classify 1/2/3; HANDOFF RETRO NO-GO; point user to NOGO prompt.

GO → doc sweep: MISSION (milestone++, checkboxes), VALIDATION [x], LOG, PLAN, ROADMAP, INDEX, README, HANDOFF retro section, ADRs. Commit message: docs: milestone [N] close — reconcile …
```

---

## Phase 5b: NO-GO — `NOGO` / `DOCFIX`

Use workflow from Missions doc: classify **1** incomplete features, **2** broken assertions, **3** docs drift. Emit paste-ready SHIP/SCRUTINY/BEHAVE/REANCHOR/RETRO/DOCFIX blocks. **Fresh RETRO** after recovery.

### PROMPT — NO-GO Recovery (abbreviated)

```
ROLE LOCK — NOGO. Read HANDOFF RETRO NO-GO, @MISSION.md, @VALIDATION.md, @docs/ROADMAP.md.
Output: CLASSIFICATION 1/2/3, ORDERED STEPS, fenced paste-ready prompts per chat (SHIP…RETRO), WHEN TO RE-RUN RETRO.
Trita paths only — no sim-studio prefix.
```

### PROMPT — Doc drift — `DOCFIX`

```
ROLE LOCK — DOCFIX. Align @PLAN.md @docs/ROADMAP.md @README.md @docs/DOCUMENTATION_INDEX.md to @HANDOFF.md + code. No feature code. Then new RETRO.
```

---

## Phase 6: Re-Anchor — `REANCHOR`

```
ROLE LOCK — REANCHOR. Read Tier A + @PLAN.md + @docs/ROADMAP.md + HANDOFF + LOG.
Report drift, VA status, root cause, 2–3 recovery options. Edit files only after user approves option.
```

---

## Full workflow summary

```
BASELINE (you)
ORCHESTRATE → MISSION / VALIDATION / PLAN sync
Per feature: SHIP → SCRUTINY → (PATCH) → BEHAVE
Per milestone: RETRO → GO doc sweep | NO-GO → NOGO → … → RETRO again
Drift: REANCHOR
```

---

## Tips (Trita-specific)

- **@MISSION.md** not drive-by edits — use HANDOFF + LOG for session detail.
- **Feature IDs** in commits/PR: `F-`*, pipelines `P-*`.
- **RM-0** needs VA-12 (no inbox) + Dagster VA-09 before RM-1.
- **RM-1** needs VA-26 (CSV hub E2E) for Yoga Bar.
- **Kill stale Worker chats** — HANDOFF is truth.
- Save each PROMPT block as a Cursor **User Rule** or snippet prefixed with trigger line.

---

## Quick reference


| Phase | Trigger     | Role         | Fresh chat    |
| ----- | ----------- | ------------ | ------------- |
| 0     | BASELINE    | You          | —             |
| 1     | ORCHESTRATE | Orchestrator | Yes           |
| 2     | SHIP        | Worker       | Yes / feature |
| 3     | SCRUTINY    | Scrutiny     | Yes           |
| 3b    | PATCH       | Fix          | If FAIL       |
| 4     | BEHAVE      | Behavioral   | Yes           |
| 5     | RETRO       | Milestone    | Yes           |
| 5b    | NOGO        | Recovery     | After NO-GO   |
| —     | DOCFIX      | Docs         | Situation 3   |
| 6     | REANCHOR    | Drift        | As needed     |


---

## Related contracts (do not duplicate here)

- Extended worker steps: [ORCHESTRATOR.md](../ORCHESTRATOR.md)
- Review checklist: [SCRUTINY.md](../SCRUTINY.md)
- Suite → VA map: [tests/BEHAVE.md](../tests/BEHAVE.md)

