# Integrations & Connector Contract

Every connector implements the same contract. Status badges must be **honest**.

---

## Integration tiers

| Tier | Mechanism | Typical apps |
|------|-----------|--------------|
| **T1** | CSV hub — schema validation + raw envelope (templates **or** column map) | Tally, Delhivery, Amazon, any merchant export |
| **T2** | Scheduled API pull | Meta, Google, GA4, Razorpay |
| **T3** | Webhooks + API | Shopify orders/inventory, Shiprocket events |

---

## Per-connector contract (mandatory)

| Field / behavior | Spec |
|----------------|------|
| `schema_version` | Semver in registry |
| Idempotency | `(tenant_id, source, external_id)` |
| Raw storage | Payload hash + `ingested_at` + lineage |
| Health | `last_sync_at`, `freshness_sla`, `status: healthy\|degraded\|failed` |
| DQ | Schema, range, referential, drift (dbt-expectations) |
| Quarantine | Hard fails → `quarantine.{source}` |

---

## Connector registry

| ID | App | Phase | Launch tier | Mode V0.0.1 |
|----|-----|-------|-------------|-------------|
| `C-SHOPIFY` | Shopify | 0–1 | **Production** | T3 API + webhooks |
| `C-UNICOMMERCE` | Unicommerce | 1 | **Production** | API or CSV |
| `C-TALLY` | Tally | 1 | **Production** | T1 CSV |
| `C-SHIPROCKET` | Shiprocket | 1 | **Production** | API or CSV |
| `C-CSV-HUB` | CSV hub | 1 | **Production** | T1 — [P-INGEST-CSV-HUB](../pipelines/P-INGEST-CSV-HUB.md); no stubs |
| `C-RAZORPAY` | Razorpay | 1 | **Production** | T2 API or CSV |
| `C-DELHIVERY` | Delhivery | 3 | Beta/CSV | T1 CSV → API |
| `C-META` | Meta Ads | 3 | Beta | T2 daily pull |
| `C-GOOGLE-ADS` | Google Ads | 3 | Beta | T2 daily pull |
| `C-GA4` | GA4 | 4 | Beta | T2 daily pull |
| `C-AMAZON` | Amazon Seller | 4 | Beta/CSV | T1 CSV → SP-API |

**Swaps:** `C-WOOCOMMERCE` (Amazon alt), `C-CASHFREE` (Razorpay alt).

---

## Freshness SLAs (defaults)

| Connector | SLA | Degraded | Failed |
|-----------|-----|----------|--------|
| Shopify inventory/orders | 4h | 8h | 24h |
| Unicommerce | 8h | 24h | 48h |
| Tally CSV | 7d manual | 14d | 30d |
| Ad platforms | 24h | 48h | 72h |
| Razorpay | 24h | 48h | 72h |

**Integrity suppress:** Shopify OR Unicommerce **failed** → no new inventory decisions.

---

## CSV hub (F-CONN-005) — production only

**Pipeline:** `P-INGEST-CSV-HUB`. Same lifecycle as API ingest: upload → validate → `raw.*` → quarantine → dbt → gold → health.

| Mode | When | Behavior |
|------|------|----------|
| **Template auto-detect** | Headers match a known `tpl_*` | Fixed map → canonical `entity_type` → schema validation |
| **Column map** | Any other CSV layout | User maps source columns → canonical fields; validation on canonical shape |
| **Saved profile** | Repeat uploads from same export tool | Per-tenant `mapping_profile` reused |

**Idempotency:** `(tenant_id, file_hash)` for upload; `(tenant_id, source, external_id, entity_type)` per row in raw.

### Templates (`tpl_*`) — convenience, not a cage

| Template ID | Typical source | Canonical `entity_type` |
|-------------|----------------|-------------------------|
| `tpl_tally_stock` | Tally | `inventory_snapshot` / `unit_cost` |
| `tpl_tally_sales` | Tally | `order_line` |
| `tpl_delhivery_shipments` | Delhivery | `shipment` |
| `tpl_amazon_orders` | Amazon | `order_line` |
| `tpl_razorpay_settlements` | Razorpay export | `payout` |
| `tpl_generic_orders` | Unknown channel | `order_line` |
| `tpl_generic_inventory` | Unknown WMS export | `inventory_snapshot` |

Arbitrary formats use **column map** + canonical validation; templates are optional accelerators.

---

## OAuth & secrets

- Stored encrypted (Supabase vault or app KMS)
- Never returned to browser
- Rotate on disconnect

## Webhook security

- HMAC per connector docs
- Idempotent processing via queue
- Replay window documented per source

See [../pipelines/REGISTRY.md](../pipelines/REGISTRY.md) for `P-INGEST-*` jobs.
