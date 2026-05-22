select
    tenant_id,
    source,
    external_id,
    entity_type,
    payload ->> 'sku' as sku,
    payload ->> 'order_id' as order_id,
    (payload ->> 'qty')::numeric as qty,
    (payload ->> 'occurred_at')::date as occurred_at,
    ingested_at
from {{ source('raw', 'csv_hub_events') }}
where entity_type = 'order_line'
