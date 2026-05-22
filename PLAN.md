# Plan: Trita V0.0.1

Product and delivery arc. **Executable truth:** [MISSION.md](MISSION.md), [docs/ROADMAP.md](docs/ROADMAP.md), [VALIDATION.md](VALIDATION.md).  
Keep this file narrative; do not duplicate feature checklists here.

---

## What we are building

**Trita** (OLynk) — web-first *Third Observer* for Indian D2C (₹5–50 Cr). One tenant-scoped graph from merchant tools, proactive **inventory decisions** in a Decision Inbox (₹ evidence, approve/reject audit), causal drivers L0–L3 **without simulation** or autonomous external writes.

**Pilot tenant for build evidence:** **Yoga Bar**.

---

## Phased delivery (16 weeks)

| Phase | RM | Weeks | Theme |
|-------|-----|-------|--------|
| 0 | RM-0 | 1–2 | Spine — Shopify E2E, Dagster shell, no inbox |
| 1 | RM-1 | 3–5 | Six apps + graph + **CSV hub production** |
| 2 | RM-2 | 6–8 | Decision Inbox + suppression |
| 3 | RM-3 | 9–11 | Causal + proactive + chat |
| 4 | RM-4 | 12–14 | Ten apps UI + hardening |
| 5 | RM-5 | 15–16 | Launch gate + commercial |

Detail: [docs/roadmap/00-overview.md](docs/roadmap/00-overview.md).

---

## Originality / non-goals (V0.0.1)

- No digital twin, forecast hero, or RL policy training
- No Tier-3 auto-write to Shopify / Unicommerce / etc.
- No mobile-first or WhatsApp-primary product
- No 25 connectors day one; no cross-tenant benchmarks
- **No connector or CSV stubs** — every production path runs validate → raw → quarantine → dbt

---

## OSS philosophy

Adopt for commodity (Postgres, dlt, dbt, Dagster, LiteLLM, DoWhy). Build in-house for decision contract, suppression, integrity gates, causal promotion policy, and tenant-scoped graph semantics.

Stack detail: [docs/OPEN_SOURCE_STACK.md](docs/OPEN_SOURCE_STACK.md) · [docs/context/stack-oss.md](docs/context/stack-oss.md).

---

## Launch definition

Product ready when [docs/checklists/LAUNCH-GATE.md](docs/checklists/LAUNCH-GATE.md) is satisfied (**VA-20**). Commercial rows (paying @ ₹10K+, pilot impact) live in that checklist, not separate VAs.

---

## How agents use this file

- **Orchestrator / RETRO:** align narrative with MISSION milestones
- **Worker:** read MISSION + VALIDATION + phase doc; PLAN is context only
- **REANCHOR:** compare PLAN phase claims vs HANDOFF/code

**Last updated:** 2026-05-22 (RM-1 closed — six apps + graph + metrics + Data Health; RM-2 Decision Inbox active)
