-- Exploded order line items for gold.fact_order_line
select
    o.tenant_id,
    o.order_id,
    o.order_name,
    o.order_updated_at,
    o.ingested_at,
    (li ->> 'id')::text as line_item_id,
    (li ->> 'variant_id')::text as variant_id,
    li ->> 'sku' as sku,
    (li ->> 'quantity')::numeric as quantity,
    (li ->> 'price')::numeric as line_price
from {{ ref('stg_shopify_orders') }} as o
cross join lateral jsonb_array_elements(
    case
        when jsonb_typeof(o.line_items) = 'array' then o.line_items
        else '[]'::jsonb
    end
) as li
