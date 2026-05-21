-- Order line grain (minimal path for VA-05)
select
    l.tenant_id,
    l.order_id,
    l.line_item_id,
    l.variant_id,
    l.sku,
    l.quantity,
    l.line_price,
    l.order_updated_at,
    l.ingested_at,
    md5(
        l.tenant_id::text || '|' || l.order_id || '|' || coalesce(l.line_item_id, '') || '|' || l.variant_id
    ) as order_line_key
from {{ ref('stg_shopify_order_lines') }} as l
where l.variant_id is not null
  and l.quantity is not null
  and l.quantity >= 0
