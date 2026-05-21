-- Rows failing staging DQ (T-P0-022 shell)
select
    'order_line_missing_variant' as failure_reason,
    l.tenant_id,
    l.order_id,
    l.line_item_id,
    l.sku,
    l.quantity,
    l.ingested_at
from "postgres"."staging"."stg_shopify_order_lines" as l
where l.variant_id is null

union all

select
    'order_line_negative_qty' as failure_reason,
    l.tenant_id,
    l.order_id,
    l.line_item_id,
    l.sku,
    l.quantity,
    l.ingested_at
from "postgres"."staging"."stg_shopify_order_lines" as l
where l.quantity < 0

union all

select
    'inventory_negative_qty' as failure_reason,
    i.tenant_id,
    i.inventory_item_id as order_id,
    null::text as line_item_id,
    null::text as sku,
    i.available_qty as quantity,
    i.ingested_at
from "postgres"."staging"."stg_shopify_inventory" as i
where i.available_qty < 0