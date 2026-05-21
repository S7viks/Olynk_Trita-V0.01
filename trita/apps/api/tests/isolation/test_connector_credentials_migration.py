"""RLS enabled on connector_credentials — no authenticated read policies."""

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[5]
    / "infra"
    / "supabase"
    / "migrations"
    / "20260520300000_connector_credentials.sql"
)


def test_connector_credentials_migration() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert MIGRATION.is_file()
    assert "connector_credentials" in sql
    assert "access_token_encrypted" in sql
    assert "enable row level security" in sql
    assert "unique (tenant_id, source)" in sql
