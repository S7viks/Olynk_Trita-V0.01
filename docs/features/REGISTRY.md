# Feature Registry

Track status in the **Status** column: `planned` | `in_progress` | `done` | `deferred`.

**Phase** = primary delivery phase. **Deps** = feature IDs that must be done first.

---

## Platform & security

| ID | Name | Phase | Status | Deps | Acceptance criteria |
|----|------|-------|--------|------|---------------------|
| F-BOOT-001 | Monorepo scaffold `trita/` | 0 | **done** | — | Layout per BUILD-ORDER #1; VA-11 |
| F-PLAT-001 | Supabase tenant + RLS | 0 | **done** | — | Membership roles; tenant scoped |
| F-PLAT-002 | Tenant isolation CI | 0 | **done** | F-PLAT-001 | Cross-tenant tests fail closed |
| F-PLAT-003 | LiteLLM proxy + budgets | 0 | **done** | — | Gemini/Groq; cap → fallback; VA-07 |
| F-PLAT-004 | OpenMeter wiring | 4 | **deferred** | F-PLAT-003 | RM-4+ / unit economics; not RM-0 |
| F-SEC-001 | Cross-tenant red team | 4 | planned | F-PLAT-002 | Documented pass |
| F-SEC-002 | Chat injection / hallucination tests | 4 | planned | F-CHAT-001 | Refuse without evidence |
| F-OPS-001 | Pilot evidence pack template | 4 | planned | F-OUTCOME-* | Weekly ₹ conservative |
| F-OPS-002 | Internal unit economics dashboard | 4 | planned | F-PLAT-004 | Per-tenant COGS/MRR |

---

## Connect & ingest

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-CONN-HEALTH | Integration health API | 0 | **done** | F-INGEST-SHOPIFY | `GET /v1/integrations/health`; VA-06 |
| F-INGEST-SHOPIFY | Shopify ingest | 0 | **done** | OAuth + API→raw; VA-05 gold path; webhooks (VA-04) deferred |
| F-CONN-001 | Shopify production | 1 | F-INGEST-SHOPIFY | Webhooks + scheduled |
| F-CONN-002 | Unicommerce | 1 | F-CONN-001 | Inventory in gold |
| F-CONN-003 | Tally CSV | 1 | F-CONN-005 | Via CSV hub; unit cost on SKU in gold |
| F-CONN-004 | Shiprocket | 1 | — | Shipments in gold |
| F-CONN-005 | CSV hub | 1 | F-GRAPH-SHELL | Template or column map → validate → raw → quarantine → gold; [P-INGEST-CSV-HUB](../pipelines/P-INGEST-CSV-HUB.md) |
| F-CONN-006 | Razorpay | 1 | — | Payouts in gold |
| F-CONN-007 | Delhivery | 3 | — | Logistics in matrix |
| F-CONN-008 | Meta Ads | 3 | — | Ad spend daily |
| F-CONN-009 | Google Ads | 3 | F-CONN-008 | Same |
| F-CONN-010 | Amazon | 4 | F-CONN-005 | CSV via hub (min); beta API ok |
| F-GA4 | GA4 connector | 4 | — | Sessions in matrix |
| F-UI-SOURCES | Sources page | 1 | F-CONN-HEALTH | 6 then 10 rows |
| F-UI-SOURCES-SHELL | Sources shell | 0 | **done** | F-CONN-HEALTH | `/sources` + health table; Shopify only in RM-0 |

Spec: [connect-sources.md](./connect-sources.md)

---

## Identity & graph

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-ID-001 | SKU alias table | 1 | F-CONN-001,002 | ≥90% lines resolve |
| F-ID-002 | Order payment/shipment bridge | 1 | F-CONN-004,006 | Join rate logged |
| F-GRAPH-SHELL | Gold table shell | 0 | **done** | staging + gold.dim_sku, fact_order_line, fact_inventory_daily; quarantine shell |
| F-METRICS-001 | velocity + cover | 1 | F-ID-001 | Matches spec |
| F-METRICS-002 | aging + dead_stock | 1 | F-METRICS-001 | Rule tests pass |
| F-METRICS-003 | stockout_risk | 1 | F-METRICS-001 | lead_time aware |
| F-METRICS-004 | capital_at_risk | 1 | F-CONN-003 | Block if no COGS |
| F-METRICS-005 | Anomaly z-score | 2 | F-METRICS-001 | Optional signal |

---

## Decisions & inbox

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-DEC-001 | Card emitter (4 types) | 2 | F-METRICS-* | JSON contract valid |
| F-DEC-002 | Suppression dedup + cap | 2 | F-DEC-001 | ≤7/week test |
| F-DEC-003 | Integrity suppress | 2 | F-CONN-HEALTH | Stale → no emit |
| F-DEC-004 | ₹ impact floors | 2 | F-METRICS-004 | Conservative doc |
| F-DEC-005 | Audit log immutable | 2 | F-DEC-001 | All actions logged |
| F-DEC-006 | outcome T+7/T+14 | 2 | F-DEC-005 | Jobs run |
| F-INBOX-001 | Inbox list | 2 | F-DEC-001 | Filter/sort |
| F-INBOX-002 | Card detail | 2 | F-INBOX-001 | Evidence links |
| F-INBOX-003 | Accept/reject/snooze | 2 | F-INBOX-002 | Enum reasons |
| F-INBOX-004 | Timeline | 2 | F-DEC-005 | Per decision |
| F-INBOX-005 | Reject reason analytics | 2 | F-INBOX-003 | Internal view |
| F-DRAFT-001 | PO draft tier-2 | 2 | F-INBOX-003 | Schema-bound LLM |
| F-DRAFT-002 | Supplier email draft | 2 | F-DRAFT-001 | On approve |
| F-DEC-BLOCKED-PRE | Unresolved SKU handling | 1 | F-ID-001 | List exportable |

Spec: [decision-inbox.md](./decision-inbox.md)

---

## Reports & UI

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-UI-NAV | 7-route navigation | 0 | **done** | — | Matches product map |
| F-UI-FEED | Home proactive feed | 2 | F-INBOX-001 | Today’s cards |
| F-UI-INVENTORY-LIST | Inventory SKU view | 1 | F-METRICS-001 | Sort aging, cover |
| F-REPORT-HEALTH | Data health report | 1 | F-CONN-HEALTH | Counts match API |
| F-REPORT-AGING | SKU aging report | 2 | F-METRICS-002 | ₹ sort |
| F-REPORT-DEAD | Dead stock report | 2 | F-METRICS-002 | Matches cards |
| F-REPORT-REORDER | Reorder queue report | 2 | F-METRICS-003 | Matches cards |

---

## Causal, proactive, chat

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-CAUSAL-001 | Association L1 | 3 | F-FEAT-MATRIX | FDR; UI label |
| F-CAUSAL-002 | DoWhy L2/L3 | 3 | F-CAUSAL-001 | Refutation gate |
| F-CAUSAL-003 | Causal narrative on card | 3 | F-CAUSAL-002, F-DEC-001 | evidence_refs |
| F-PROACTIVE-001 | Trigger engine | 3 | F-DEC-001 | Feed populate |
| F-PROACTIVE-002 | Monday digest | 3 | F-PROACTIVE-001 | Top 3 |
| F-PROACTIVE-003 | Email digest | 3 | F-PROACTIVE-001 | ≤1 urgent/day |
| F-PROACTIVE-004 | Slack digest | 3 | F-PROACTIVE-003 | Optional |
| F-CHAT-001 | Inventory chat API | 3 | F-PLAT-003 | Grounded refuse |
| F-CHAT-002 | Chat UI | 3 | F-CHAT-001 | Evidence chips |
| F-FEAT-MATRIX | SKU-week matrix | 3 | F-CONN-007,008 | Completeness score |

Spec: [causal-proactive.md](./causal-proactive.md)

---

## Settings, legal, billing

| ID | Name | Phase | Deps | Acceptance criteria |
|----|------|-------|------|---------------------|
| F-SETTINGS-001 | Lead times + notifications | 2 | — | Affects reorder |
| F-LEGAL-001 | Privacy policy | 5 | — | Published |
| F-LEGAL-002 | Terms | 5 | — | Published |
| F-LEGAL-003 | DPA outline | 5 | — | Sales doc |
| F-LEGAL-004 | Tenant deletion | 5 | — | Workflow + SLA |
| F-BILLING-001 | ₹10K+ billing | 5 | — | Charge succeeds |
| F-ONBOARD-001 | Day 0–7 checklist | 5 | F-UI-SOURCES | In-app + ops doc |

---

## Feature ↔ pipeline map

| Feature | Pipelines |
|---------|-----------|
| F-INGEST-* | P-INGEST-{SOURCE} |
| F-METRICS-* | P-METRICS-DAILY, P-METRICS-INTRADAY |
| F-DEC-* | P-DECISION-EMIT |
| F-CAUSAL-* | P-FEAT-MATRIX-WEEKLY, P-CAUSAL-DOWHY |
| F-PROACTIVE-* | P-DIGEST-EMAIL, P-DIGEST-SLACK |

Full list: [../pipelines/REGISTRY.md](../pipelines/REGISTRY.md)
