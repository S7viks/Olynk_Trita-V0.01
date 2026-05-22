select
    l.tenant_id,
    l.order_line_key,
    l.order_id,
    l.line_item_id,
    l.variant_id,
    l.sku,
    l.quantity,
    l.line_price,
    a.canonical_sku_id,
    a.confidence as alias_confidence,
    a.source as alias_source,
    (a.canonical_sku_id is not null) as is_resolved
from {{ ref('fact_order_line') }} as l
left join {{ ref('bridge_sku_alias') }} as a
    on l.tenant_id = a.tenant_id
    and a.source = 'shopify'
    and a.external_id = l.variant_id
