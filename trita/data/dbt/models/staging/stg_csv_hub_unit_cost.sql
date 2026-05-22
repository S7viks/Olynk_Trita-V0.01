-- Tally / CSV hub unit cost rows (F-CONN-005 → F-CONN-003)
select
    tenant_id,
    source,
    external_id,
    entity_type,
    payload ->> 'sku' as sku,
    (payload ->> 'unit_cost')::numeric as unit_cost,
    (payload ->> 'as_of')::date as as_of,
    ingested_at
from {{ source('raw', 'csv_hub_events') }}
where entity_type = 'unit_cost'
  and source in ('tally', 'generic')
