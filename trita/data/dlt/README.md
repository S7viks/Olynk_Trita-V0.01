# data/dlt

dlt ingest for Trita. All connectors write the **raw envelope** (`tenant_id`, `source`, `external_id`, `entity_type`, `payload`, `payload_hash`, `lineage`).

## Shopify (T-P0-010, T-P0-011)

Migration: `infra/supabase/migrations/20260520200000_raw_shopify_events.sql` → `raw.shopify_events`.

```bash
cd trita/data/dlt
pip install -e ".[dev]"

# Unit tests (no DB)
pytest tests/test_envelope.py tests/test_shopify_pipeline.py tests/test_raw_migration_contract.py -q

# Load Yoga Bar fixture into raw (requires migrations + tenant row + DATABASE_URL)
export DATABASE_URL=postgresql://...
python -m trita_dlt.shopify.run --tenant-id <yoga-bar-tenant-uuid>
```

Pilot fixture: `src/trita_dlt/shopify/fixtures/yoga_bar_sample.json`.

## Idempotency (T-P0-013)

Unique `(tenant_id, source, external_id, entity_type)` — replays are no-op (`ON CONFLICT DO NOTHING`).
