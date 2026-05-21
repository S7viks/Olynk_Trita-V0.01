# Pipeline: P-CAUSAL-DOWHY (+ P-CAUSAL-ASSOC)

**Phase:** 3  
**Package:** `packages/causal/`

---

## Purpose

Promote association candidates to L2/L3 causal edges with DoWhy refutation — **no simulation**.

---

## Inputs

- `feat.sku_week_matrix` (required completeness ≥ threshold)
- Association edges from `P-CAUSAL-ASSOC`
- `policy.yaml` ontology blocklist

---

## Outputs

```sql
-- analytics.causal_edges
tenant_id, sku_id, cause_variable, effect_variable,
evidence_type,  -- association | causal_candidate | causal_verified
lag_days, confidence, refutation_status, refutation_details jsonb,
n_weeks, completeness, promoted_at
```

---

## P-CAUSAL-ASSOC (precursor)

| Step | Detail |
|------|--------|
| 1 | For each SKU with n_weeks ≥ min |
| 2 | Pairwise lagged correlation (0..14d) on matrix columns |
| 3 | Benjamini-Hochberg FDR across pairs |
| 4 | Emit edges above threshold with `evidence_type=association` |
| 5 | Apply ontology prior — drop blocked pairs |

---

## P-CAUSAL-DOWHY

| Step | Detail |
|------|--------|
| 1 | Select top-K association edges per SKU (cap cost) |
| 2 | Build causal model from template family (see policy) |
| 3 | `identify_effect` → `estimate_effect` |
| 4 | Refutation battery: placebo, random common cause, subset stability |
| 5 | If all pass + completeness OK → `causal_verified` (L3) |
| 6 | If estimate ok but refutation fail → `causal_candidate` (L2) |
| 7 | Attach edge ids to decision cards via `AG-CAU` → `AG-DEC` |

---

## Model templates (examples)

| Template ID | Treatment | Outcome | Confounders |
|-------------|-----------|---------|-------------|
| `ad_to_velocity` | ad_spend_lag7 | velocity_7d | seasonality_week |
| `rto_to_cover` | rto_rate | days_of_cover | velocity_30d |
| `inv_divergence` | shopify_uni_delta | stockout_risk | velocity_7d |

Add templates only with PM + data sign-off.

---

## Runtime guards

- Max SKUs per tenant per run (e.g. 500) — prioritize by capital_at_risk
- Max wall clock 90m — spillover to next run
- Skip if integrity suppress

---

## LLM usage

- **After** promotion only: Gemini explains edge in card copy
- Prompt includes: layer, refutation summary, `evidence_refs`, disclaimers
- **No** DoWhy inside LLM

---

## Acceptance

- [ ] Fixture SKU with known assoc → L1 label correct
- [ ] Failed refutation stays L2, never L3 in UI
- [ ] 0 edges cross-tenant
- [ ] OpenMeter logs runtime seconds (custom meter optional)

See [../context/causal-policy.md](../context/causal-policy.md).
