select
    e.tenant_id,
    e.external_id as shipment_id,
    e.payload ->> 'order_id' as order_id,
    e.payload ->> 'channel_order_id' as channel_order_id,
    e.payload ->> 'status' as shipment_status,
    e.payload ->> 'awb' as awb,
    e.ingested_at
from {{ source('raw', 'shiprocket_events') }} as e
where e.entity_type = 'shipment'
