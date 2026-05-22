# Phase 1 — Six Apps + Graph (Weeks 3–5)

**Status (2026-05-22):** **Closed** — RM-1 GO; evidence `scripts/verify_rm1_gate.py` (VA-13/14/26). See [HANDOFF.md](../../HANDOFF.md) RETRO Milestone 2.

**Goal:** Wide enough graph for inventory truth.

**Exit:** Data Health Card accurate for **Yoga Bar**; ≥90% order lines resolve identity.

---

## Connectors (production-grade)

| # | Connector | Mode | Task focus |
|---|-----------|------|------------|
| 1 | `C-SHOPIFY` | API + webhooks | Harden Phase 0 |
| 2 | `C-UNICOMMERCE` | API or CSV | Warehouse inventory |
| 3 | `C-TALLY` | CSV | COGS, unit cost |
| 4 | `C-SHIPROCKET` | API or CSV | Shipments |
| 5 | `C-CSV-HUB` | Templates | Generic + Amazon prep |
| 6 | `C-RAZORPAY` | API or CSV | Settlements |

---

## Work packages

### WP1-A — Connectors 2–6

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P1-001 | Unicommerce dlt tap + staging | Inventory in `gold.fact_inventory_daily` |
| T-P1-002 | Tally via CSV hub (`tpl_tally_*`) | Unit cost on SKU where provided |
| T-P1-003 | Shiprocket ingest | `gold.fact_shipment` populated |
| T-P1-004 | Razorpay ingest | `gold.fact_payout` populated |
| T-P1-005 | CSV hub production: upload, template detect, column map, validate, raw→gold | Yoga Bar: tpl **or** arbitrary CSV; quarantine visible; [P-INGEST-CSV-HUB](../pipelines/P-INGEST-CSV-HUB.md) |

**Features:** `F-CONN-002`..`F-CONN-006`  
**Pipelines:** `P-INGEST-*` per connector

---

### WP1-B — Identity resolution v1

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P1-010 | `sku_alias` table + merge API stub | Aliases stored |
| T-P1-011 | Shopify ↔ Unicommerce matcher (rules + manual queue later) | ≥90% order lines resolved |
| T-P1-012 | Order bridge: payment + shipment ids | Join rate logged |
| T-P1-013 | Blocked SKU report for ops | Unresolved list exportable |

**Features:** `F-ID-001`, `F-ID-002`, `F-DEC-BLOCKED-PRE`  
**Package:** `packages/ontology/identity.py`

---

### WP1-C — Gold graph + DQ

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P1-020 | Complete gold models (see data-graph.md) | dbt docs generated |
| T-P1-021 | Integration health mart | `feat.integration_health` |
| T-P1-022 | Integrity score per tenant | Feeds suppress flag (Phase 2) |
| T-P1-023 | Quarantine dashboard (internal) | Ops can see failed rows |

**Pipelines:** `P-DBT-DAILY`, `P-DQ-QUARANTINE`

---

### WP1-D — Deterministic metrics job

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P1-030 | `feat.sku_metrics_daily` job | velocity, cover, aging |
| T-P1-031 | stockout_risk + dead_stock flags | Match SQL spec in data-graph |
| T-P1-032 | capital_at_risk with COGS gate | Missing COGS → null impact |
| T-P1-033 | Nightly schedule + intraday Shopify/Uni | Schedules documented |

**Features:** `F-METRICS-001`..`F-METRICS-005`  
**Pipelines:** `P-METRICS-DAILY`, `P-METRICS-INTRADAY`

---

### WP1-E — Product surfaces (data)

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P1-040 | Sources UI: 6 connectors + badges | honest status |
| T-P1-041 | Data Health Report | Matches backend counts |
| T-P1-042 | Inventory SKU list (read-only) | Sort by aging, cover |

**Features:** `F-UI-SOURCES`, `F-REPORT-HEALTH`, `F-UI-INVENTORY-LIST`

---

## Deliverables checklist

- [x] 6 connectors ingesting for pilot tenant
- [x] ≥90% order line resolution
- [x] Gold tables populated
- [x] DQ quarantine active
- [x] Deterministic metrics live
- [x] Data Health Report matches API

---

## Pilot onboarding (start)

- Day 0: Shopify + Unicommerce connect
- Day 1–3: Tally CSV, Razorpay
- Day 4–7: Shiprocket; validate health card

---

## References

- [../context/integrations.md](../context/integrations.md)
- [../context/data-graph.md](../context/data-graph.md)
- [../features/connect-sources.md](../features/connect-sources.md)
