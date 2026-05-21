"""VA-02 (integration): cross-tenant SELECT fails under RLS when DB is configured."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import pytest

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.skipif(
    os.environ.get("TRITA_RUN_ISOLATION") != "1",
    reason="Set TRITA_RUN_ISOLATION=1 and DATABASE_URL to run Postgres RLS integration tests",
)

MIGRATION = (
    Path(__file__).resolve().parents[5]
    / "infra"
    / "supabase"
    / "migrations"
    / "20260520100000_tenants_memberships.sql"
)

TENANT_A = UUID("11111111-1111-1111-1111-111111111101")
TENANT_B = UUID("22222222-2222-2222-2222-222222222202")
USER_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture(scope="module")
def db_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    with psycopg.connect(url, autocommit=True) as conn:
        yield conn


@pytest.fixture(scope="module", autouse=True)
def _apply_migration(db_conn) -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    with db_conn.cursor() as cur:
        cur.execute(sql)


@pytest.fixture(scope="module", autouse=True)
def _seed_isolation_rows(db_conn) -> None:
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.tenants (id, slug, display_name) VALUES
              (%s, 'tenant-a', 'Tenant A'),
              (%s, 'tenant-b', 'Tenant B')
            ON CONFLICT (slug) DO NOTHING
            """,
            (TENANT_A, TENANT_B),
        )
        for tenant_id, user_id in ((TENANT_A, USER_A), (TENANT_B, USER_B)):
            try:
                cur.execute(
                    """
                    INSERT INTO public.memberships (tenant_id, user_id, role)
                    VALUES (%s, %s, 'owner')
                    ON CONFLICT (tenant_id, user_id) DO NOTHING
                    """,
                    (tenant_id, user_id),
                )
            except psycopg.errors.ForeignKeyViolation as exc:
                pytest.skip(
                    "memberships require auth.users rows — use Supabase test users "
                    f"({exc})"
                )


def _as_user(cur, user_id: UUID) -> None:
    cur.execute("SET LOCAL role authenticated")
    cur.execute(
        "SELECT set_config('request.jwt.claim.sub', %s, true)",
        (str(user_id),),
    )
    cur.execute(
        "SELECT set_config('request.jwt.claim.role', 'authenticated', true)",
    )


def test_user_a_cannot_read_tenant_b(db_conn) -> None:
    with db_conn.cursor() as cur:
        _as_user(cur, USER_A)
        cur.execute(
            "SELECT id FROM public.tenants WHERE id = %s",
            (TENANT_B,),
        )
        rows = cur.fetchall()
    assert rows == []


def test_user_b_cannot_read_tenant_a(db_conn) -> None:
    with db_conn.cursor() as cur:
        _as_user(cur, USER_B)
        cur.execute(
            "SELECT id FROM public.tenants WHERE id = %s",
            (TENANT_A,),
        )
        rows = cur.fetchall()
    assert rows == []


def test_user_a_can_read_own_tenant(db_conn) -> None:
    with db_conn.cursor() as cur:
        _as_user(cur, USER_A)
        cur.execute(
            "SELECT id FROM public.tenants WHERE id = %s",
            (TENANT_A,),
        )
        rows = cur.fetchall()
    assert len(rows) == 1
