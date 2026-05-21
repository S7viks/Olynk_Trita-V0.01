# Master Plan Traceability

Maps **master plan sections** → **docs artifacts** → **implementation artifacts** (when built). Use during reviews to find gaps.

---

## Section → doc map

| Plan § | Topic | Context | Roadmap | Features | Pipelines |
|--------|-------|---------|---------|----------|-----------|
| 0 | Executive summary | MASTER-CONTEXT | 00-overview | REGISTRY | — |
| 1 | Vision | MASTER-CONTEXT | — | — | — |
| 2 | Scope in/out | MASTER-CONTEXT | phase files | REGISTRY | — |
| 3 | 10 apps | integrations.md | P1, P3, P4 | F-CONN-* | P-INGEST-* |
| 4 | Architecture | architecture.md | 00-overview | — | REGISTRY DAG |
| 5 | Data plane | data-graph.md, integrations.md | P0–P1 | F-ID-*, F-METRICS-* | P-INGEST-*, P-DBT-* |
| 6 | Analytics | data-graph.md | P1–P2 | F-METRICS-* | P-METRICS-* |
| 7 | Causal | causal-policy.md | P3 | F-CAUSAL-* | P-CAUSAL-* |
| 8 | Decisions | decision-contract.md | P2 | F-DEC-*, F-INBOX-* | P-DECISION-EMIT |
| 9 | Surfaces | product-surfaces.md | P2–P3 | F-UI-*, F-REPORT-* | — |
| 10 | Agents | agents.md | P2–P3 | (roles in AGENTS.md) | job wiring |
| 11 | OSS | stack-oss.md | P0 | F-PLAT-* | — |
| 12 | Unit economics | stack-oss.md | P0, P4 | F-OPS-002, F-PLAT-004 | P-METER-EXPORT |
| 13 | Security | MASTER-CONTEXT, LAUNCH-GATE | P0, P4 | F-SEC-*, F-PLAT-002 | — |
| 14 | Commercial | phase-5-launch.md | P5 | F-BILLING-*, F-LEGAL-* | — |
| 15 | 16-week build | phase-0..5 | all | REGISTRY | REGISTRY |
| 16 | Post-V0.0.1 | phase-5-launch.md | — | deferred | — |
| 17 | Team roles | MASTER-CONTEXT | — | — | — |
| 18 | Success metrics | MASTER-CONTEXT | phase-exit | — | — |
| 19 | Risks | 00-overview | — | — | — |
| 20 | Launch checklist | LAUNCH-GATE.md | P5 | — | — |
| 21 | Launch publish | phase-5-launch.md | P5 | — | — |

---

## Decision card type traceability

| Plan type | ID | Feature | Pipeline |
|-----------|-----|---------|----------|
| INVENTORY_REORDER | D-REORDER | F-DEC-001 | P-DECISION-EMIT |
| INVENTORY_DEAD_STOCK | D-DEAD | F-DEC-001 | P-DECISION-EMIT |
| INVENTORY_CAPITAL_TRAP | D-CAPITAL | F-DEC-001 | P-DECISION-EMIT |
| INVENTORY_BLOCKED | D-BLOCKED | F-DEC-001 | P-DECISION-EMIT |

---

## Connector traceability

| Plan # | Connector ID | Phase | Production at launch? |
|--------|--------------|-------|---------------------|
| 1 | C-SHOPIFY | 0–1 | Yes |
| 2 | C-UNICOMMERCE | 1 | Yes |
| 3 | C-TALLY | 1 | Yes (CSV) |
| 4 | C-SHIPROCKET | 1 | Yes |
| 5 | C-DELHIVERY | 3 | Beta/CSV |
| 6 | C-RAZORPAY | 1 | Yes |
| 7 | C-META | 3 | Beta |
| 8 | C-GOOGLE-ADS | 3 | Beta |
| 9 | C-GA4 | 4 | Beta |
| 10 | C-AMAZON | 4 | Beta/CSV |

---

## Known doc stubs (expand when implementing)

| File | Expand when |
|------|-------------|
| `pipelines/P-INGEST-*.md` (except Shopify) | Connector build starts |
| `docs/ops/red-team-*.md` | Phase 4 |
| `docs/commercial/evidence-pack-template.md` | Phase 4 |
| `packages/*` README | Package scaffold |

---

## Gap watch (intentionally deferred)

| Item | Target version |
|------|----------------|
| WhatsApp digest | V0.0.2 |
| Mobile approve | V0.0.2 |
| Logistics cards UI | V0.0.3 |
| Tier-3 external writes | V0.2.0 |
| 25 connectors | V1.0 |
| Cross-tenant benchmarks | Not planned V0.0.1 |

If any gap appears in **V0.0.1 launch gate** without a row above, treat as a **planning bug** and add to REGISTRY.
