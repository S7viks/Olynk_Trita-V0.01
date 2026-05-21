-- Inventory levels (not full product documents)
select
    e.tenant_id,
    e.external_id as inventory_item_id,
    e.ingested_at,
    (e.payload ->> 'available')::numeric as available_qty,
    (e.payload ->> 'updated_at')::timestamptz as level_updated_at,
    e.lineage
from "postgres"."raw"."shopify_events" as e
where e.source = 'shopify'
  and e.entity_type = 'inventory'
  and e.payload ? 'inventory_item_id'
  and not (e.payload ? 'variants')