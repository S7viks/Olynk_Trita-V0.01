-- Shopify product payloads (Admin API products.json)
select
    e.tenant_id,
    e.external_id as product_id,
    e.ingested_at,
    e.payload ->> 'title' as product_title,
    e.payload ->> 'handle' as product_handle,
    e.payload -> 'variants' as variants,
    e.lineage
from "postgres"."raw"."shopify_events" as e
where e.source = 'shopify'
  and e.entity_type = 'inventory'
  and e.payload ? 'variants'