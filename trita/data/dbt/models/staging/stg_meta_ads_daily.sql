select
    e.tenant_id,
    (e.payload ->> 'date')::date as spend_date,
    e.payload ->> 'campaign_id' as campaign_id,
    (e.payload ->> 'spend')::numeric as spend_inr,
    e.ingested_at
from {{ source('raw', 'meta_ads_events') }} as e
where e.entity_type = 'ad_spend_daily'
