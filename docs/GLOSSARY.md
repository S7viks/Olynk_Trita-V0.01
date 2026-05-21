# Glossary — Trita V0.0.1

Shared vocabulary for Cursor agents and engineers.

| Term | Meaning |
|------|---------|
| **Third Observer** | Product positioning — observes merchant systems, does not replace ERP/WMS |
| **Trita** | Product name (OLynk) |
| **Yoga Bar** | Primary pilot tenant for E2E and milestone evidence |
| **RM-*** | Program roadmap milestone (RM-0 … RM-5) in [ROADMAP.md](./ROADMAP.md) |
| **VA-*** | Validation assertion in [VALIDATION.md](../VALIDATION.md) |
| **F-*** | Feature ID in [features/REGISTRY.md](./features/REGISTRY.md) |
| **P-*** | Pipeline / Dagster job ID |
| **T-P{n}-*** | Phase task in `docs/roadmap/phase-*.md` |
| **C-*** | Connector ID (e.g. `C-SHOPIFY`) |
| **Raw envelope** | `tenant_id`, `source`, `external_id`, `payload`, `payload_hash`, `lineage` |
| **Quarantine** | Hard-fail rows excluded from gold; visible in health UI |
| **CSV hub** | `F-CONN-005` — any CSV via template or column map; no stubs |
| **Integrity suppress** | No new inventory decisions if Shopify or Unicommerce past SLA |
| **Suppression** | Dedup `(tenant, type, sku, week)` + ≤7 cards / 7 days |
| **L0–L3** | Causal label tiers; L3 only after DoWhy refutation |
| **Tier 1/2/3** | Connector integration depth — CSV / API pull / webhooks (see integrations.md) |
| **Tier-2 draft** | LLM-generated PO/email on approve — human executes |
| **Tier 3** | Auto-write to external systems — **disabled** in V0.0.1 |
| **Deterministic engine** | dbt + packages own all inventory numbers; LLM language only |
| **HANDOFF** | Shared log between Cursor chats — session state, not chat history |
