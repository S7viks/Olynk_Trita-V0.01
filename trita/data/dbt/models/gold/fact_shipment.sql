select
    s.tenant_id,
    s.shipment_id,
    s.order_id,
    s.channel_order_id,
    s.shipment_status,
    s.awb,
    s.ingested_at::date as shipment_date,
    md5(s.tenant_id::text || '|' || s.shipment_id) as shipment_key
from {{ ref('stg_shiprocket_shipments') }} as s
where s.shipment_id is not null
