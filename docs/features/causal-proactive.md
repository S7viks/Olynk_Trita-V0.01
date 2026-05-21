# Feature: Causal, Proactive, Chat

**IDs:** `F-CAUSAL-*`, `F-PROACTIVE-*`, `F-CHAT-*`  
**Phase:** 3

---

## Causal on cards

Display rules from [causal-policy.md](../context/causal-policy.md):

| Layer | UI copy pattern |
|-------|-----------------|
| L0 | "On hand: X · Cover: Y days" |
| L1 | "Correlated with Meta spend (lag 7d, r=0.62)" |
| L2 | "Hypothesis: RTO rate may be reducing effective cover" + assumptions |
| L3 | "Tested driver: Ad spend lag (passed refutation)" |

Never show L3 without `refutation_status: pass` in data.

---

## Proactive triggers

| Trigger ID | Condition | Action |
|------------|-----------|--------|
| TR-COVER | cover < lead_time × 1.2 | Emit REORDER candidate |
| TR-VEL-DELTA | velocity_7d down >40% vs 30d | Feed highlight |
| TR-CAUSAL | L2/L3 promoted | Feed + optional email |
| TR-SYNC-FAIL | connector failed | Feed alert, suppress decisions |
| TR-DIGEST-MON | Monday 9am IST | Top 3 open cards email |

**Email caps:** max 1 urgent/day; 1 weekly digest.

---

## Chat (inventory only)

**Allowed topics:** SKU cover, reorder rationale, dead stock, report drill-down, integration freshness.

**Refuse when:**

- SKU not in tenant graph
- Integrity suppress active
- User asks for non-inventory domains (ads strategy, legal, etc.)
- Missing evidence_refs for factual claim

**Flow:**

1. Resolve SKU / intent
2. Load ContextProjection (cache)
3. Retrieve evidence chunks (pgvector)
4. Groq for latency; Gemini for long explanation if needed
5. Return answer + `evidence_refs[]`

---

## Acceptance tests

- [ ] Card shows L1 without claiming causation
- [ ] L3 hidden when refutation fails
- [ ] Chat: "What should I reorder for SKU-X?" → grounded or refuse
- [ ] Chat: "Write my ad strategy" → refuse scope
- [ ] Email digest contains only tenant's cards
