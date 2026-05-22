-- Latest unit cost per tenant × sku from CSV hub (Tally path)
select distinct on (tenant_id, sku)
    tenant_id,
    sku as sku_code,
    unit_cost,
    as_of,
    source,
    ingested_at as updated_at,
    md5(tenant_id::text || '|' || sku || '|' || source) as unit_cost_key
from {{ ref('stg_csv_hub_unit_cost') }}
where sku is not null
  and unit_cost is not null
order by tenant_id, sku, as_of desc nulls last, ingested_at desc
