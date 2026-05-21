
  
    

  create  table "postgres"."gold"."dim_sku__dbt_tmp"
  
  
    as
  
  (
    -- Canonical SKU shell from Shopify variants (SCD1 for V0.0.1)
select
    tenant_id,
    variant_id as shopify_variant_id,
    product_id as shopify_product_id,
    coalesce(nullif(trim(sku), ''), variant_id) as sku_code,
    coalesce(variant_title, product_title) as title,
    inventory_quantity,
    ingested_at as updated_at,
    md5(tenant_id::text || '|' || variant_id) as sku_key
from "postgres"."staging"."stg_shopify_product_variants"
where variant_id is not null
  );
  