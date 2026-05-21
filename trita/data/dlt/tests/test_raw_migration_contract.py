from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "infra"
    / "supabase"
    / "migrations"
    / "20260520200000_raw_shopify_events.sql"
)


def test_raw_shopify_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_raw_envelope_columns_and_dedup() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "create schema if not exists raw" in sql
    assert "payload_hash" in sql
    assert "lineage" in sql
    assert "shopify_events_dedup" in sql or "unique (tenant_id, source, external_id, entity_type)" in sql
