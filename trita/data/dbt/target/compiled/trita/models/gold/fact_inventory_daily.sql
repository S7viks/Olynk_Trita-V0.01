-- SKU × day inventory shell from Shopify inventory levels
select
    i.tenant_id,
    i.inventory_item_id,
    coalesce(i.level_updated_at::date, i.ingested_at::date) as inventory_date,
    i.available_qty as on_hand,
    i.ingested_at,
    md5(
        i.tenant_id::text || '|' || i.inventory_item_id || '|'
        || coalesce(i.level_updated_at::date, i.ingested_at::date)::text
    ) as inventory_daily_key
from "postgres"."staging"."stg_shopify_inventory" as i
where i.available_qty is not null
  and i.available_qty >= 0