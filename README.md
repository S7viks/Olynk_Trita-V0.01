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

**Phase:** RM-1 — six apps + graph (Weeks 3–5)  
**Monorepo:** `trita/` — Phase 0 spine complete (see [HANDOFF.md](HANDOFF.md) RM-0 gate)  
**Next action:** [docs/BUILD-ORDER.md](docs/BUILD-ORDER.md) — connectors `F-CONN-002`–`006` or CSV hub `F-CONN-005`

## Quick copy

```bash
cp .env.example .env
# Fill Supabase + API keys — never commit .env or .env.local
```

## License

Proprietary — OLynk.
