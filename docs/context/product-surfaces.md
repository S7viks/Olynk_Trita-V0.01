# Product Surfaces (Web V0.0.1)

Seven primary routes. **Inbox-first** onboarding after auth.

---

## Navigation map

| # | Route | Name | Phase | Primary features |
|---|-------|------|-------|------------------|
| 1 | `/` | Home / Proactive feed | 2 | F-UI-FEED, F-PROACTIVE-001 |
| 2 | `/inbox` | Decision Inbox | 2 | F-INBOX-* |
| 3 | `/sources` | Sources | 0–4 | F-UI-SOURCES, F-CONN-* |
| 4 | `/inventory` | Inventory | 1–2 | F-UI-INVENTORY-LIST, F-METRICS-* |
| 5 | `/reports` | Reports | 1–2 | F-REPORT-* |
| 6 | `/chat` | Chat | 3 | F-CHAT-* |
| 7 | `/settings` | Settings | 2–3 | F-SETTINGS-001, notifications |

---

## Onboarding flow (Day 0–7)

| Day | User action | System response |
|-----|-------------|-----------------|
| 0 | Sign up, create tenant | Empty health card |
| 0–1 | Connect Shopify | Ingest + green row |
| 1–2 | Connect Unicommerce | Inventory truth |
| 2–3 | Upload Tally CSV | COGS where available |
| 3–4 | Razorpay + Shiprocket | Payouts + shipments |
| 5–7 | Wait for metrics + first card | Email optional Phase 3 |

Checklist feature: `F-ONBOARD-001` (Phase 5 hardening, start in Phase 1).

---

## Reports (secondary to inbox)

| Report | Route | Sort default |
|--------|-------|--------------|
| SKU aging | `/reports/aging` | ₹ at risk desc |
| Dead stock | `/reports/dead-stock` | aging desc |
| Reorder queue | `/reports/reorder` | stockout_risk desc |
| Data health | `/reports/health` | worst connector first |

Each row links to `evidence_refs` / source drill-down.

---

## Out of scope on these routes (V0.0.1)

- Logistics module UI (data only in graph)
- Finance working capital UI
- Custom dashboards / arbitrary widgets
- Mobile layout optimization
