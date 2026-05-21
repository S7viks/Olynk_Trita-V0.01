# Causal Intelligence Policy

**V0.0.1: No simulation.** Association + ontology priors + DoWhy refutation only.

---

## Epistemic layers (UI labels)

| Layer | UI label | On card? | Backend |
|-------|----------|----------|---------|
| L0 | Fact | Always | Deterministic metrics |
| L1 | Correlated with | Yes | Association scan + FDR correction |
| L2 | Hypothesized driver | Yes + assumptions | DoWhy estimate, refutation pending |
| L3 | Tested driver | Only after refutation pass | DoWhy refute: pass |

**Gemini may explain L2 and L3 only** with tier-appropriate disclaimer. L1 uses “correlated with”, never “causes”.

---

## Pipeline stages

```mermaid
flowchart LR
  M[SKU-week matrix] --> A[Association scan]
  A --> O[Ontology prior filter]
  O --> W[DoWhy identify + estimate]
  W --> R[Refutation battery]
  R --> P{Promote L3?}
  P -->|yes| CARD[Decision card reasoning]
  P -->|no| L2[L2 hypothesis only]
```

### 1. Feature matrix

- Grain: `SKU × ISO week`
- Columns: inventory, velocity, ad_spend, RTO rate, payout delay, sessions
- Minimum `n_weeks` per SKU: **12** (configurable)

### 2. Association scan

- Lagged correlation (configurable lags 0–14d)
- Multiple testing correction (Benjamini-Hochberg or similar)
- Output: candidate edges with `evidence_type: association`

### 3. Ontology prior (block list)

Examples of **blocked** edges without extra evidence:

- Ad spend → COGS directly
- Payout timing → SKU on-hand without order path
- Implausible lag > 21d for velocity

### 4. DoWhy

- Model per hypothesis family (documented templates)
- Identify → estimate → **refute**:
  - placebo treatment
  - random common cause
  - data subset stability

### 5. Promotion L2 → L3

All required:

- Refutation battery pass
- Data completeness ≥ threshold (e.g. 0.7)
- `n_weeks` ≥ minimum
- No integrity suppress active

---

## Inventory causal questions (examples)

| Question | Mechanism |
|----------|-----------|
| Unicommerce vs Shopify divergence | False cover → `D-BLOCKED` or L1 divergence |
| Ad spend spike → velocity lag 5–9d | L1 lagged corr → L2/L3 if refuted |
| RTO rise → effective sell-through drop | Logistics features in matrix |
| Tally COGS missing | Block ₹ impact; L0 facts only |

---

## Product copy guardrails

| Allowed | Forbidden |
|---------|-----------|
| “Correlated with ad spend (lag 7d)” | “Ads caused stockout” |
| “Hypothesis: RTO may be reducing effective cover” | “Definitely because of RTO” |
| “Tested driver (passed refutation)” | “Proven causal effect ₹X” without floor methodology |

---

## Service ownership

| Component | Owner package |
|-----------|---------------|
| `feat.sku_week_matrix` build | `data/dbt` + job |
| Association scanner | `packages/causal/association.py` |
| DoWhy runner | `packages/causal/dowhy_runner.py` |
| Promotion policy | `packages/causal/policy.yaml` |
| Card injection | `packages/decisions/enrich.py` |

---

## Config knobs (store in `policy.yaml`)

```yaml
min_weeks: 12
completeness_threshold: 0.7
max_lags_days: 14
fdr_alpha: 0.05
refutation_tests:
  - placebo
  - random_common_cause
  - subset_stability
```

See [../pipelines/P-CAUSAL-DOWHY.md](../pipelines/P-CAUSAL-DOWHY.md).
