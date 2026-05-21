
  create view "postgres"."staging"."stg_shopify_product_variants__dbt_tmp"
    
    
  as (
    -- Variant rows from product payloads → dim_sku seed
select
    p.tenant_id,
    p.product_id,
    p.product_title,
    (v ->> 'id')::text as variant_id,
    v ->> 'sku' as sku,
    v ->> 'title' as variant_title,
    (v ->> 'inventory_quantity')::numeric as inventory_quantity,
    p.ingested_at
from "postgres"."staging"."stg_shopify_products" as p
cross join lateral jsonb_array_elements(
    case
        when jsonb_typeof(p.variants) = 'array' then p.variants
        else '[]'::jsonb
    end
) as v
  );