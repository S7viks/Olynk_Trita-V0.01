# Supabase migrations

SQL migrations with RLS on every tenant table. Apply via Supabase CLI or MCP.

| File | Purpose |
|------|---------|
| `20260520100000_tenants_memberships.sql` | `tenants`, `memberships`, RLS (`F-PLAT-001`) |
| `20260520100001_seed_yoga_bar_dev.sql` | Pilot tenant slug `yoga-bar` |
| `20260520200000_raw_shopify_events.sql` | `raw.shopify_events` envelope (`F-INGEST-SHOPIFY`) |
| `20260520300000_connector_credentials.sql` | Encrypted Shopify OAuth tokens per tenant |

JWT claims for API: `sub`, `tenant_id`, `role` (see `trita/apps/api/src/trita_api/auth.py`).
