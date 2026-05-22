# Trita V0.0.1 (OLynk)

**Third Observer** — connected intelligence OS for Indian D2C inventory decisions.

This repository is the **ground-up build** workspace. Application code will live under `trita/` as phases progress; planning and context live in `docs/`.

## Start here

| Document | Purpose |
|----------|---------|
| [MISSION.md](MISSION.md) | Mission, milestones, feature priority |
| [VALIDATION.md](VALIDATION.md) | Done = VA assertions pass |
| [docs/README.md](docs/README.md) | Documentation hub |
| [docs/context/MASTER-CONTEXT.md](docs/context/MASTER-CONTEXT.md) | Product truth |
| [docs/BUILD-ORDER.md](docs/BUILD-ORDER.md) | Implementation sequence |
| [docs/ROADMAP.md](docs/ROADMAP.md) | RM-0 … RM-5 program gates |
| [docs/roadmap/00-overview.md](docs/roadmap/00-overview.md) | 16-week phases |
| [AGENTS.md](AGENTS.md) | Rules for AI agents |
| [docs/CURSOR-MULTI-AGENT-WORKFLOW.md](docs/CURSOR-MULTI-AGENT-WORKFLOW.md) | Cursor triggers (`SHIP`, `SCRUTINY`, …) |
| [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | Agent reading order |

## Status

**Phase:** RM-2 — Decision Inbox + suppression (Weeks 6–8)  
**Monorepo:** `trita/` — RM-0 + RM-1 complete for Yoga Bar (see [HANDOFF.md](HANDOFF.md) RETRO 2026-05-22)  
**Next action:** [docs/BUILD-ORDER.md](docs/BUILD-ORDER.md) — `F-DEC-001`..`004` decision contract + emitter

## Quick copy

```bash
cp .env.example .env
# Fill Supabase + API keys — never commit .env or .env.local
```

## License

Proprietary — OLynk.
