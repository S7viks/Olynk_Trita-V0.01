# data/dbt

dbt project: **raw** → **staging** → **gold** (+ **quarantine**). Feature `F-GRAPH-SHELL`, pipeline `P-DBT-DAILY`.

## Models

| Layer | Models |
|-------|--------|
| staging | `stg_shopify_orders`, `stg_shopify_order_lines`, `stg_shopify_inventory`, `stg_shopify_products`, `stg_shopify_product_variants` |
| gold | `dim_sku`, `fact_order_line`, `fact_inventory_daily` |
| quarantine | `shopify_invalid` |

## Prerequisites

1. Migrations applied (`20260520400000_graph_schemas.sql` for `staging`, `gold`, `quarantine` schemas).
2. Yoga Bar data in `raw.shopify_events` (Shopify OAuth + sync).

## Run (from repo root)

```bash
pip install -e "trita/data/dbt[dev]"
python scripts/run_dbt.py run
python scripts/run_dbt.py test
```

Uses `DATABASE_URL` from `.env` (pooler URL is fine).

## VA-05 integration test

```bash
TRITA_RUN_VA05=1 pytest trita/data/dbt/tests/test_va05_yoga_bar.py -q
```

Profiles: `profiles/profiles.yml` (env vars only; no secrets in git). See `profiles.example.yml` for local copy.
