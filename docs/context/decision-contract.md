# Decision System Contract

## Card types (V0.0.1 only)

| ID | Type | Priority | Trigger examples |
|----|------|----------|------------------|
| `D-REORDER` | `INVENTORY_REORDER` | P0 | `stockout_risk`, cover < lead time |
| `D-DEAD` | `INVENTORY_DEAD_STOCK` | P0 | dead_stock rule |
| `D-CAPITAL` | `INVENTORY_CAPITAL_TRAP` | P1 | high capital_at_risk, slow velocity |
| `D-BLOCKED` | `INVENTORY_BLOCKED` | P0 | identity, COGS, stale sync |

---

## Minimum card JSON schema

```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "type": "INVENTORY_REORDER",
  "sku_id": "canonical_sku_id",
  "event": "stockout_risk",
  "impact": {
    "inr_floor": 0,
    "horizon_days": 14,
    "assumptions": ["lead_time_days=12"]
  },
  "reasoning": {
    "causal_chain": [],
    "evidence_refs": ["feat.sku_metrics_daily:..."],
    "missing_data": [],
    "epistemic_layer": "L0"
  },
  "recommendation": {
    "action_template": "create_po_draft",
    "parameters": { "qty": 120, "supplier_id": "..." }
  },
  "confidence": {
    "completeness": 0.85,
    "staleness_hours": 4,
    "gated": false
  },
  "inaction_model": {
    "inr_at_risk_if_ignored": 45000,
    "days_to_stockout": 6
  },
  "execution": { "tier": 1 },
  "provenance_links": [],
  "suppression_key": "tenant:type:sku:week",
  "created_at": "iso8601"
}
```

---

## Suppression rules

| Rule | Spec |
|------|------|
| Dedup key | `(tenant_id, type, sku_id, ISO week)` |
| Weekly cap | ≤7 **new** cards / 7 rolling days / tenant |
| Integrity suppress | If Shopify OR Unicommerce `last_sync_at` > SLA → no new inventory cards |
| Snooze | User snooze respects dedup; re-surface after snooze window |

---

## Reject reasons (enum, required on reject)

- `wrong_qty`
- `wrong_sku_mapping`
- `already_ordered`
- `supplier_issue`
- `promo_planned`
- `data_stale`
- `not_actionable`
- `other` (+ optional text)

---

## Autonomy tiers

| Tier | V0.0.1 behavior |
|------|-----------------|
| 1 | Suggest / manual steps only |
| 2 | PO draft, supplier email draft → DB artifact + timeline |
| 3 | **Disabled** — no external auto-write |

---

## Audit log (immutable)

```json
{
  "decision_id": "uuid",
  "user_id": "uuid",
  "action": "approved | rejected | snoozed | draft_created",
  "reason_enum": "wrong_qty",
  "reason_text": null,
  "projection_hash": "sha256",
  "timestamp": "iso8601"
}
```

**Rule:** `projection_hash` covers metrics snapshot used for card — enables outcome comparison T+7/T+14.

---

## Outcome scheduler

| Checkpoint | Job | Compare |
|------------|-----|---------|
| T+7 | `outcome_eval_7d` | Projected vs actual cover, stockout |
| T+14 | `outcome_eval_14d` | Same + acceptance attribution |

Feeds pilot evidence pack (₹ conservative methodology).

---

## LLM on cards

- Gemini via LiteLLM: narrative, causal explanation
- Must cite `evidence_refs[]` or refuse
- Never override deterministic `recommendation.parameters`

See [causal-policy.md](./causal-policy.md) for L0–L3 display rules.
