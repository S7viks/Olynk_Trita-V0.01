-- Deterministic SKU metrics (F-METRICS-001..004) — engine-owned, no LLM math
{{ config(
    materialized='table',
    tags=['metrics', 'daily']
) }}

with params as (
    select
        current_date as metric_date,
        {{ var('lead_time_days', 14) }}::numeric as lead_time_days,
        (1.0 / 7.0)::numeric as velocity_dead_stock_threshold
),

skus as (
    select
        d.tenant_id,
        d.sku_key as canonical_sku_id,
        d.sku_code,
        coalesce(d.inventory_quantity, 0)::numeric as shopify_on_hand
    from {{ ref('dim_sku') }} as d
),

uni_on_hand as (
    select
        a.tenant_id,
        a.canonical_sku_id,
        sum(u.available_qty)::numeric as on_hand
    from {{ ref('stg_unicommerce_inventory') }} as u
    inner join {{ ref('bridge_sku_alias') }} as a
        on u.tenant_id = a.tenant_id
        and a.source = 'unicommerce'
        and a.external_id = u.sku_code
    group by 1, 2
),

unit_costs as (
    select
        tenant_id,
        sku_code,
        unit_cost
    from {{ ref('sku_unit_cost') }}
),

sales as (
    select
        r.tenant_id,
        r.canonical_sku_id,
        l.order_updated_at::date as sale_date,
        sum(l.quantity)::numeric as qty
    from {{ ref('fact_order_line_resolved') }} as r
    inner join {{ ref('fact_order_line') }} as l
        on r.order_line_key = l.order_line_key
    where r.is_resolved
      and r.canonical_sku_id is not null
    group by 1, 2, 3
),

velocity as (
    select
        s.tenant_id,
        s.canonical_sku_id,
        coalesce(
            sum(
                case
                    when s.sale_date >= p.metric_date - interval '7 days' then s.qty
                    else 0
                end
            ) / 7.0,
            0
        )::numeric as velocity_7d,
        coalesce(
            sum(
                case
                    when s.sale_date >= p.metric_date - interval '30 days' then s.qty
                    else 0
                end
            ) / 30.0,
            0
        )::numeric as velocity_30d,
        max(s.sale_date) as last_sale_date
    from sales as s
    cross join params as p
    group by 1, 2
),

assembled as (
    select
        sk.tenant_id,
        p.metric_date,
        sk.canonical_sku_id,
        sk.sku_code,
        coalesce(u.on_hand, sk.shopify_on_hand, 0)::numeric as on_hand,
        coalesce(v.velocity_7d, 0)::numeric as velocity_7d,
        coalesce(v.velocity_30d, 0)::numeric as velocity_30d,
        case
            when coalesce(v.velocity_7d, 0) > 0
                then coalesce(u.on_hand, sk.shopify_on_hand, 0) / v.velocity_7d
            else null
        end::numeric as days_of_cover,
        case
            when v.last_sale_date is null then 999
            else (p.metric_date - v.last_sale_date)::integer
        end as aging_days,
        uc.unit_cost,
        p.lead_time_days,
        p.velocity_dead_stock_threshold
    from skus as sk
    cross join params as p
    left join uni_on_hand as u
        on sk.tenant_id = u.tenant_id
        and sk.canonical_sku_id = u.canonical_sku_id
    left join velocity as v
        on sk.tenant_id = v.tenant_id
        and sk.canonical_sku_id = v.canonical_sku_id
    left join unit_costs as uc
        on sk.tenant_id = uc.tenant_id
        and sk.sku_code = uc.sku_code
)

select
    tenant_id,
    metric_date,
    canonical_sku_id,
    sku_code,
    on_hand,
    velocity_7d,
    velocity_30d,
    days_of_cover,
    aging_days,
    unit_cost,
    lead_time_days,
    (
        velocity_7d > 0
        and days_of_cover is not null
        and days_of_cover < lead_time_days * 1.2
    ) as stockout_risk,
    (
        aging_days > 90
        and velocity_7d < velocity_dead_stock_threshold
    ) as dead_stock,
    case
        when unit_cost is not null then on_hand * unit_cost
        else null
    end::numeric as capital_at_risk,
    (unit_cost is null) as cogs_missing,
    greatest(
        0::numeric,
        ceil(coalesce(velocity_7d, 0) * lead_time_days - on_hand)
    )::numeric as reorder_qty,
    now() at time zone 'utc' as computed_at,
    md5(tenant_id::text || '|' || canonical_sku_id || '|' || metric_date::text) as metrics_daily_key
from assembled
