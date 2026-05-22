select
    e.tenant_id,
    e.external_id as settlement_id,
    e.payload ->> 'entity_id' as payment_id,
    e.payload ->> 'channel_order_id' as channel_order_id,
    coalesce((e.payload ->> 'amount')::bigint, 0) as amount_paise,
    e.payload ->> 'currency' as currency,
    e.payload ->> 'status' as settlement_status,
    e.ingested_at
from {{ source('raw', 'razorpay_events') }} as e
where e.entity_type = 'payout'
