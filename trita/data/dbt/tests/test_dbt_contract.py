"""dbt project contract tests (CI without Postgres)."""

from __future__ import annotations

from pathlib import Path

DBT_ROOT = Path(__file__).resolve().parents[1]
MODELS = DBT_ROOT / "models"


def test_dbt_project_file_exists() -> None:
    assert (DBT_ROOT / "dbt_project.yml").is_file()


def test_staging_models_present() -> None:
    staging = MODELS / "staging"
    names = {
        "stg_shopify_orders.sql",
        "stg_shopify_order_lines.sql",
        "stg_shopify_inventory.sql",
        "stg_shopify_products.sql",
        "stg_shopify_product_variants.sql",
    }
    assert names.issubset({p.name for p in staging.glob("*.sql")})


def test_gold_shell_models_present() -> None:
    gold = MODELS / "gold"
    assert (gold / "dim_sku.sql").is_file()
    assert (gold / "fact_order_line.sql").is_file()
    assert (gold / "fact_inventory_daily.sql").is_file()


def test_quarantine_model_present() -> None:
    assert (MODELS / "quarantine" / "shopify_invalid.sql").is_file()


def test_staging_references_raw_source() -> None:
    orders = (MODELS / "staging" / "stg_shopify_orders.sql").read_text(encoding="utf-8")
    assert "source('raw', 'shopify_events')" in orders
    assert "entity_type = 'order'" in orders


def test_gold_models_filter_tenant_grain() -> None:
    dim = (MODELS / "gold" / "dim_sku.sql").read_text(encoding="utf-8")
    assert "tenant_id" in dim
    fact = (MODELS / "gold" / "fact_order_line.sql").read_text(encoding="utf-8")
    assert "tenant_id" in fact
