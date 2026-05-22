# Phase 3 — Causal + Proactive (Weeks 9–11)

**Goal:** Third Observer differentiation — drivers on cards, proactive feed, digests, grounded chat.

**Exit:** One card shows L2 or L3 driver with evidence (e.g. ad lag or RTO).

---

## Additional connectors

| Connector | Mode | Week |
|-----------|------|------|
| `C-DELHIVERY` | CSV/API | 9 |
| `C-META` | API daily | 10 |
| `C-GOOGLE-ADS` | API daily | 10 |

---

## Work packages

### WP3-A — Feature matrix

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P3-001 | `feat.sku_week_matrix` build | Ads + logistics + payouts joined |
| T-P3-002 | Completeness score per SKU-week | Gates causal run |
| T-P3-003 | Minimum weeks enforcement | n≥12 default |

**Pipeline:** `P-FEAT-MATRIX-WEEKLY`

---

### WP3-B — Association (L1)

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P3-010 | Lagged correlation scanner | FDR correction |
| T-P3-011 | Store edges with `evidence_type: association` | Queryable per SKU |
| T-P3-012 | UI: "Correlated with" on card | Never "causes" |

**Features:** `F-CAUSAL-001`  
**Package:** `packages/causal/association.py`

---

### WP3-C — DoWhy (L2/L3)

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P3-020 | DoWhy runner + policy.yaml | Refutation battery |
| T-P3-021 | Ontology prior blocklist | Implausible edges dropped |
| T-P3-022 | L2 → L3 promotion gate | Tests pass on fixture |
| T-P3-023 | Gemini narrative with disclaimers | evidence_refs required |

**Features:** `F-CAUSAL-002`, `F-CAUSAL-003`  
**Pipeline:** `P-CAUSAL-DOWHY`  
**Agent:** `AG-CAU`

---

### WP3-D — Proactive

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P3-030 | Triggers: threshold, delta, causal promotion, sync fail | Feed populates |
| T-P3-031 | Monday digest job | Top 3 decisions |
| T-P3-032 | Email: weekly + urgent (max 1/day) | Unsubscribe |
| T-P3-033 | Slack digest (optional) | Same content as email |

**Features:** `F-PROACTIVE-001`..`F-PROACTIVE-004`  
**Pipelines:** `P-DIGEST-EMAIL`, `P-DIGEST-SLACK`

---

### WP3-E — Narrow chat

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P3-040 | Inventory-scoped chat API | Refuse if incomplete data |
| T-P3-041 | ContextProjection + pgvector retrieval | Groq fast path |
| T-P3-042 | Chat UI with evidence chips | No general knowledge answers |

**Features:** `F-CHAT-001`, `F-CHAT-002`

---

## Example acceptance scenarios

| Scenario | Expected layer |
|----------|----------------|
| Ad spend ↑, velocity ↑ 7d later | L1 on card; L3 if refutation passes |
| RTO rate ↑, cover overstated | L2 hypothesis |
| Shopify vs Uni qty mismatch | L1 + optional BLOCKED |
| COGS missing | BLOCKED for ₹; L0 only |

---

## Deliverables checklist

- [x] SKU-week matrix for pilot _(dbt `feat.sku_week_matrix`; empty until gold weeks + RM-3 connector sync)_
- [x] L1 correlations on ≥1 card type _(pipeline + `analytics.causal_edges`; pilot may use L2 seed when n&lt;12w)_
- [x] ≥1 L2 or L3 driver on pilot card _(RM-3 gate 2026-05-22 — `verify_rm3_gate.py`)_
- [x] Proactive feed auto-populate
- [ ] Email digest sent in staging _(log-only without Resend)_
- [x] Chat refuses hallucination test cases _(pytest `test_chat.py`)_

---

## References

- [../context/causal-policy.md](../context/causal-policy.md)
- [../pipelines/P-CAUSAL-DOWHY.md](../pipelines/P-CAUSAL-DOWHY.md)
- [../features/causal-proactive.md](../features/causal-proactive.md)
