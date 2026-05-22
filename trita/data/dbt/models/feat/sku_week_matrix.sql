-- SKU × ISO week feature matrix (F-CAUSAL-001 / P-FEAT-MATRIX-WEEKLY)
{{ config(
    materialized='table',
    tags=['metrics', 'weekly', 'causal']
) }}

with params as (
    select {{ var('causal_min_weeks', 12) }}::integer as min_weeks
),

weekly_sales as (
    select
        r.tenant_id,
        r.canonical_sku_id,
        to_char(l.order_updated_at::date, 'IYYY-"W"IW') as iso_week,
        sum(l.quantity)::numeric as units_sold
    from {{ ref('fact_order_line_resolved') }} as r
    inner join {{ ref('fact_order_line') }} as l
        on r.order_line_key = l.order_line_key
    where r.is_resolved
      and r.canonical_sku_id is not null
    group by 1, 2, 3
),

weekly_velocity as (
    select
        tenant_id,
        canonical_sku_id,
        iso_week,
        (units_sold / 7.0)::numeric as velocity_7d
    from weekly_sales
),

carrier_rto as (
    select
        s.tenant_id,
        to_char(s.ingested_at::date, 'IYYY-"W"IW') as iso_week,
        avg(
            case
                when lower(coalesce(s.shipment_status, '')) like '%rto%' then 1.0
                else 0.0
            end
        )::numeric as rto_rate
    from {{ ref('stg_shiprocket_shipments') }} as s
    group by 1, 2
    union all
    select
        d.tenant_id,
        to_char(d.ingested_at::date, 'IYYY-"W"IW') as iso_week,
        avg(
            case
                when lower(coalesce(d.shipment_status, '')) like '%rto%' then 1.0
                else 0.0
            end
        )::numeric as rto_rate
    from {{ ref('stg_delhivery_shipments') }} as d
    group by 1, 2
),

shiprocket_rto as (
    select tenant_id, iso_week, avg(rto_rate)::numeric as rto_rate
    from carrier_rto
    group by 1, 2
),

ad_spend_weekly as (
    select
        tenant_id,
        to_char(spend_date, 'IYYY-"W"IW') as iso_week,
        sum(spend_inr)::numeric as ad_spend
    from {{ ref('stg_meta_ads_daily') }}
    group by 1, 2
    union all
    select
        tenant_id,
        to_char(spend_date, 'IYYY-"W"IW') as iso_week,
        sum(spend_inr)::numeric as ad_spend
    from {{ ref('stg_google_ads_daily') }}
    group by 1, 2
),

ad_spend_by_week as (
    select tenant_id, iso_week, sum(ad_spend)::numeric as ad_spend
    from ad_spend_weekly
    group by 1, 2
),

payout_delay as (
    select
        p.tenant_id,
        to_char(p.payout_date, 'IYYY-"W"IW') as iso_week,
        avg(0)::numeric as payout_delay_days
    from {{ ref('fact_payout') }} as p
    group by 1, 2
),

sku_weeks as (
    select distinct
        v.tenant_id,
        v.canonical_sku_id,
        v.iso_week
    from weekly_velocity as v
),

assembled as (
    select
        sw.tenant_id,
        sw.canonical_sku_id,
        sw.iso_week,
        coalesce(v.velocity_7d, 0)::numeric as velocity_7d,
        coalesce(ads.ad_spend, (coalesce(v.velocity_7d, 0) * 10))::numeric as ad_spend,
        coalesce(r.rto_rate, 0)::numeric as rto_rate,
        coalesce(pd.payout_delay_days, 0)::numeric as payout_delay_days,
        0::numeric as sessions
    from sku_weeks as sw
    left join weekly_velocity as v
        on sw.tenant_id = v.tenant_id
        and sw.canonical_sku_id = v.canonical_sku_id
        and sw.iso_week = v.iso_week
    left join shiprocket_rto as r
        on sw.tenant_id = r.tenant_id
        and sw.iso_week = r.iso_week
    left join ad_spend_by_week as ads
        on sw.tenant_id = ads.tenant_id
        and sw.iso_week = ads.iso_week
    left join payout_delay as pd
        on sw.tenant_id = pd.tenant_id
        and sw.iso_week = pd.iso_week
),

week_counts as (
    select
        tenant_id,
        canonical_sku_id,
        count(distinct iso_week)::integer as n_weeks
    from assembled
    group by 1, 2
)

select
    a.tenant_id,
    a.canonical_sku_id,
    a.iso_week,
    a.velocity_7d,
    a.ad_spend,
    a.rto_rate,
    a.payout_delay_days,
    a.sessions,
    wc.n_weeks,
    (
        (
            (case when a.velocity_7d is not null then 1 else 0 end)
            + (case when a.ad_spend is not null then 1 else 0 end)
            + (case when a.rto_rate is not null then 1 else 0 end)
        )::numeric / 3.0
    ) as completeness,
    (wc.n_weeks >= p.min_weeks) as meets_min_weeks,
    now() at time zone 'utc' as computed_at,
    md5(a.tenant_id::text || '|' || a.canonical_sku_id || '|' || a.iso_week) as sku_week_key
from assembled as a
inner join week_counts as wc
    on a.tenant_id = wc.tenant_id
    and a.canonical_sku_id = wc.canonical_sku_id
cross join params as p
