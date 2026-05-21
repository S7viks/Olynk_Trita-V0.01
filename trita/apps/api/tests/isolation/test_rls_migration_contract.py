"""VA-02 (CI): migration defines RLS policies that block cross-tenant reads."""

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[5]
    / "infra"
    / "supabase"
    / "migrations"
    / "20260520100000_tenants_memberships.sql"
)


def test_tenants_memberships_migration_exists() -> None:
    assert MIGRATION.is_file(), f"missing migration: {MIGRATION}"


def test_rls_enabled_on_tenant_tables() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "alter table public.tenants" in sql
    assert "alter table public.memberships" in sql


def test_tenant_select_policy_scoped_to_membership() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "tenants_select_member" in sql
    assert "auth.uid()" in sql
    assert "memberships" in sql


def test_memberships_select_policy_own_rows_only() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "memberships_select_own" in sql
    assert "user_id = auth.uid()" in sql
