-- Orders from raw.shopify_events (entity_type = order)
select
    e.tenant_id,
    e.external_id as order_id,
    e.ingested_at,
    e.payload ->> 'name' as order_name,
    (e.payload ->> 'updated_at')::timestamptz as order_updated_at,
    e.payload -> 'line_items' as line_items,
    e.lineage
from {{ source('raw', 'shopify_events') }} as e
where e.source = 'shopify'
  and e.entity_type = 'order'
