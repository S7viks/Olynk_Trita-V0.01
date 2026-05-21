# Program Roadmap (RM-*)

Granular program milestones for **Milestone Review** and **VALIDATION.md** gates. Phase detail lives in [`roadmap/`](./roadmap/); this file is the index.

---

## Milestones

| ID | Weeks | Exit headline | Phase doc | Blocking VAs | ADR / gates |
|----|-------|---------------|-----------|--------------|-------------|
| **RM-0** | 1–2 | Yoga Bar: Shopify E2E + health row; no inbox | [phase-0-spine.md](./roadmap/phase-0-spine.md) | VA-01, VA-02, VA-05, VA-06, VA-07, VA-09, VA-10, VA-11, VA-12 | [ADR-001](./adr/001-orchestrator.md) **Accepted (Dagster)** |
| **RM-1** | 3–5 | Yoga Bar: Data Health accurate; ≥90% order lines resolved; CSV hub E2E | [phase-1-six-apps-graph.md](./roadmap/phase-1-six-apps-graph.md) | VA-13, VA-14, VA-26 | [P-INGEST-CSV-HUB](./pipelines/P-INGEST-CSV-HUB.md) |
| **RM-2** | 6–8 | Yoga Bar: accept/reject ≥1 card; suppression verified | [phase-2-inventory-inbox.md](./roadmap/phase-2-inventory-inbox.md) | VA-15, VA-16, VA-17 | — |
| **RM-3** | 9–11 | Yoga Bar: ≥1 card with L2 or L3 driver + evidence | [phase-3-causal-proactive.md](./roadmap/phase-3-causal-proactive.md) | VA-18, VA-19 | [causal-policy.md](./context/causal-policy.md) |
| **RM-4** | 12–14 | 10 sources in UI; red team + load docs | [phase-4-ten-apps-hardening.md](./roadmap/phase-4-ten-apps-hardening.md) | VA-21, VA-22, VA-23 | — |
| **RM-5** | 15–16 | Launch gate pass; product ready to ship | [phase-5-launch.md](./roadmap/phase-5-launch.md) | VA-20 (+ checklist commercial rows) | [LAUNCH-GATE.md](./checklists/LAUNCH-GATE.md) |

---

## RM-0 acceptance (Phase 0 spine)

**Status (2026-05-21):** Program gate closed — `python scripts/verify_rm0_gate.py` exit 0; MISSION item 15 checked. **VA-10** (Render 7d) and **VA-08** (OpenMeter) remain deferred per VALIDATION.

**RM-1 is active** (RETRO 2026-05-21). RM-0 prerequisites met:

1. **RM-0 blocking VAs** checked in [`../VALIDATION.md`](../VALIDATION.md) _(VA-10, VA-04, VA-08 deferred per contract)_.
2. **ADR-001** **Accepted** (Dagster).
3. Evidence: `scripts/verify_rm0_gate.py` exit 0; Sources `/sources` Shopify row healthy for Yoga Bar.

---

## RM-5 launch gate

Maps to [`checklists/LAUNCH-GATE.md`](./checklists/LAUNCH-GATE.md). Milestone Review for RM-5 blocks GO until launch checklist is fully checked or waived with sign-off.

---

## Related

| Doc | Role |
|-----|------|
| [BUILD-ORDER.md](./BUILD-ORDER.md) | Dependency-ordered implementation items |
| [roadmap/00-overview.md](./roadmap/00-overview.md) | 16-week timeline and risks |
| [checklists/phase-exit-criteria.md](./checklists/phase-exit-criteria.md) | Quick phase gate table |
| [../MISSION.md](../MISSION.md) | Mission milestones 1–6 (1:1 with RM-0…RM-5); pilot: Yoga Bar |
