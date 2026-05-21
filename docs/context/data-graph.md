# Data Graph Model

**Pattern:** Wide storage, narrow UX. Inventory subgraph drives product; extended subgraph feeds causal/proactive.

---

## Inventory subgraph (UX-facing)

| Entity | Key fields | Sources |
|--------|------------|---------|
| `SKU` | `canonical_sku_id`, aliases, title, category | Shopify variant, Unicommerce SKU, Tally item |
| `InventoryPosition` | `on_hand`, `committed`, `location`, `as_of` | Shopify, Unicommerce |
| `Order` | `channel_order_id`, `ordered_at`, `status` | Shopify, Amazon |
| `OrderLine` | `sku_id`, `qty`, `revenue` | Orders |
| `Supplier` | `name`, `lead_time_days` | Settings + future ERP |
| `SupplierSKU` | `supplier_id`, `sku_id`, `moq`, `unit_cost` | Tally, manual |

---

## Extended subgraph (causal / proactive)

| Entity | Purpose |
|--------|---------|
| `Shipment`, `Return`, `RTO` | Logistics lag, effective sell-through |
| `Payout`, `Settlement` | Cash timing |
| `AdCampaign`, `AdSpend` | Demand lag 5–9d |
| `Session` | GA4 traffic priors |

---

## Edge metadata (all causal edges)

```yaml
evidence_type: fact | association | causal_candidate | causal_verified
lag_days: int
refutation_status: pending | pass | fail
confidence: float  # 0-1, policy-gated display
source_refs: string[]  # lineage ids
```

---

## Identity resolution (critical)

### SKU aliases

| Source | External key | Maps to |
|--------|--------------|---------|
| Shopify | `variant_id` | `canonical_sku_id` |
| Unicommerce | `sku_code` | `canonical_sku_id` |
| Tally | `item_code` | `canonical_sku_id` |

**Table:** `sku_alias(tenant_id, source, external_id, canonical_sku_id, confidence, merged_by)`

**Rule:** No decision on unresolved identity → `D-BLOCKED` card with `missing_data: ["sku_identity"]`.

### Order linking

`channel_order_id` ↔ `payment_id` (Razorpay) ↔ `shipment_id` (Shiprocket)

**Target Phase 1:** ≥90% order lines resolve.

---

## Gold layer tables (dbt naming convention)

| Table | Grain | Notes |
|-------|-------|-------|
| `gold.dim_sku` | SKU | SCD1 for V0.0.1 |
| `gold.fact_inventory_daily` | SKU × day × location | |
| `gold.fact_order_line` | Line | |
| `gold.fact_shipment` | Shipment | Phase 1+ |
| `gold.fact_ad_spend_daily` | Campaign × day | Phase 3 |
| `gold.fact_payout` | Payout | Phase 1 |
| `gold.bridge_sku_alias` | Alias | |

---

## Feature tables (analytics)

| Table | Grain | Consumer |
|-------|-------|----------|
| `feat.sku_week_matrix` | SKU × ISO week | Association, DoWhy |
| `feat.sku_metrics_daily` | SKU × day | Deterministic engine |
| `feat.integration_health` | Source × tenant | Sources UI, suppress |

---

## Deterministic metrics (owned by engine)

| Metric | Definition |
|--------|------------|
| `velocity_7d`, `velocity_30d` | Rolling order line qty / day |
| `days_of_cover` | `on_hand / avg_daily_sales` |
| `aging_days` | Days since last sale movement |
| `stockout_risk` | `cover < lead_time * 1.2` |
| `dead_stock` | `aging > 90d` AND `velocity < 1/week` |
| `capital_at_risk` | `on_hand * unit_cost` (block if COGS missing) |
| `reorder_qty` | Cover-based; lower confidence without lead time |

Optional: **statsforecast** demand bands — not hero ML in V0.0.1.

---

## Integrity gates

| Condition | Behavior |
|-----------|----------|
| Shopify OR Unicommerce stale > SLA | Suppress all inventory decisions |
| COGS missing | Block ₹ impact; show fact-only |
| SKU unresolved | `INVENTORY_BLOCKED` |
| Divergence Shopify vs Unicommerce > threshold | Causal candidate + warning card |

---

## pgvector (V0.0.1 minimal)

- Embed decision narratives + report snippets for chat retrieval
- Not used for numeric decisions

See [decision-contract.md](./decision-contract.md), [causal-policy.md](./causal-policy.md).
