select
    e.tenant_id,
    e.external_id,
    e.payload ->> 'sku_code' as sku_code,
    coalesce((e.payload ->> 'available_qty')::numeric, 0) as available_qty,
    e.payload ->> 'facility' as facility,
    e.ingested_at
from {{ source('raw', 'unicommerce_events') }} as e
where e.entity_type = 'inventory'
  and e.payload ->> 'sku_code' is not null
