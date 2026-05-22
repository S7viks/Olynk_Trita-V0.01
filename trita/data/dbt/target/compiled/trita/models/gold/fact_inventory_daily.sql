-- SKU × day inventory: Shopify + Unicommerce (F-CONN-002)
with shopify_inv as (
    select
        i.tenant_id,
        i.inventory_item_id as sku_ref,
        'shopify' as inventory_source,
        coalesce(i.level_updated_at::date, i.ingested_at::date) as inventory_date,
        i.available_qty as on_hand,
        i.ingested_at
    from "postgres"."staging"."stg_shopify_inventory" as i
    where i.available_qty is not null
      and i.available_qty >= 0
),
unicommerce_inv as (
    select
        u.tenant_id,
        u.sku_code as sku_ref,
        'unicommerce' as inventory_source,
        u.ingested_at::date as inventory_date,
        u.available_qty as on_hand,
        u.ingested_at
    from "postgres"."staging"."stg_unicommerce_inventory" as u
    where u.available_qty is not null
      and u.available_qty >= 0
),
combined as (
    select * from shopify_inv
    union all
    select * from unicommerce_inv
)
select
    tenant_id,
    sku_ref,
    inventory_source,
    inventory_date,
    on_hand,
    ingested_at,
    md5(
        tenant_id::text || '|' || inventory_source || '|' || sku_ref || '|' || inventory_date::text
    ) as inventory_daily_key
from combined