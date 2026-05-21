# Pipeline: P-INGEST-SHOPIFY

**Phase:** 0 (bootstrap) → 1 (harden)  
**Tier:** T3 — webhooks + scheduled API  
**Connector:** `C-SHOPIFY`

---

## Purpose

Load Shopify **orders**, **order lines**, and **inventory levels** into raw envelope with lineage for dbt.

---

## Inputs

| Resource | API / webhook | Entities |
|----------|---------------|----------|
| Orders | `orders/updated` webhook + backfill | Order, OrderLine |
| Inventory | REST + webhook | InventoryLevel per variant |
| Products | daily sync | Variant → SKU alias seed |

---

## Raw envelope schema

```sql
-- raw.shopify_events
tenant_id uuid NOT NULL,
source text DEFAULT 'shopify',
external_id text NOT NULL,
entity_type text NOT NULL,  -- order | inventory | product
payload jsonb NOT NULL,
payload_hash text NOT NULL,
ingested_at timestamptz NOT NULL,
lineage jsonb  -- { shop_domain, api_version, webhook_id }
```

**Unique:** `(tenant_id, source, external_id, entity_type)`

---

## Steps

1. **Authenticate** — per-tenant OAuth token from vault
2. **Incremental** — `updated_at_min` from watermark table
3. **Webhook path** — verify HMAC → enqueue → same normalizer as batch
4. **Normalize** — map to envelope; compute hash; skip if hash unchanged
5. **Watermark** — update per shop per entity_type
6. **Health** — write `feat.integration_health` row

---

## dbt downstream

| Staging model | Gold |
|---------------|------|
| `stg_shopify_orders` | `gold.fact_order_line` |
| `stg_shopify_inventory` | `gold.fact_inventory_daily` |
| `stg_shopify_products` | `gold.dim_sku` (partial) |

---

## DQ checks

- `order_id` not null
- `variant_id` not null on lines
- `qty` >= 0
- `updated_at` within 365d

Failures → `quarantine.shopify`

---

## OpenMeter events

- `connector_sync_rows` count
- `connector_api_calls` per run

---

## Failure modes

| Failure | Behavior |
|---------|----------|
| 401 auth | status=failed; no decision emit (via health) |
| Rate limit | exponential backoff; degraded if partial |
| Parse error | quarantine row; continue batch |

---

## Test fixtures

- `fixtures/shopify/order_single.json`
- `fixtures/shopify/inventory_levels.json`
- Webhook replay script in `scripts/replay_shopify_webhook.py` (create Phase 0)
