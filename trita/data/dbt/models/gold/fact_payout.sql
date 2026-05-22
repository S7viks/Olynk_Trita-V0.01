select
    p.tenant_id,
    p.settlement_id,
    p.payment_id,
    p.channel_order_id,
    p.amount_paise,
    p.currency,
    p.settlement_status,
    p.ingested_at::date as payout_date,
    md5(p.tenant_id::text || '|' || p.settlement_id) as payout_key
from {{ ref('stg_razorpay_payouts') }} as p
where p.settlement_id is not null
