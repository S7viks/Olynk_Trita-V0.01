"""Postgres helpers — always filter by tenant_id from JWT."""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    return url


@dataclass(frozen=True)
class ConnectorCredential:
    tenant_id: UUID
    source: str
    account_ref: str | None
    access_token: str
    scopes: str | None


@dataclass(frozen=True)
class ShopifyCredential:
    tenant_id: UUID
    shop_domain: str
    access_token: str
    scopes: str | None


def upsert_shopify_credential(
    *,
    tenant_id: UUID,
    shop_domain: str,
    access_token_encrypted: str,
    scopes: str | None,
) -> None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.connector_credentials (
                    tenant_id, source, shop_domain, access_token_encrypted, scopes, updated_at
                ) VALUES (%s, 'shopify', %s, %s, %s, now())
                ON CONFLICT (tenant_id, source) DO UPDATE SET
                    shop_domain = EXCLUDED.shop_domain,
                    access_token_encrypted = EXCLUDED.access_token_encrypted,
                    scopes = EXCLUDED.scopes,
                    updated_at = now()
                """,
                (tenant_id, shop_domain, access_token_encrypted, scopes),
            )


@dataclass(frozen=True)
class TenantMembership:
    tenant_id: UUID
    role: str
    tenant_slug: str | None


@dataclass(frozen=True)
class TenantOnboarding:
    tenant_id: UUID
    display_name: str
    slug: str
    onboarding_complete: bool
    shopify_connected: bool


def _slugify_base(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return base[:40] or "tenant"


def provision_tenant_for_user(
    *,
    user_id: UUID,
    email: str,
    display_name: str | None = None,
) -> TenantMembership:
    """Create tenant + owner membership for a new Supabase user (service DB path)."""
    label = (display_name or email.split("@")[0] or "Workspace").strip()[:120]
    slug_base = _slugify_base(email.split("@")[0] or label)
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for attempt in range(8):
                slug = slug_base if attempt == 0 else f"{slug_base}-{secrets.token_hex(3)}"
                cur.execute(
                    """
                    INSERT INTO public.tenants (slug, display_name, owner_email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (slug) DO NOTHING
                    RETURNING id
                    """,
                    (slug, label, email.strip().lower()),
                )
                row = cur.fetchone()
                if row:
                    tenant_id = row[0]
                    break
            else:
                raise RuntimeError("Could not allocate unique tenant slug")

            cur.execute(
                """
                INSERT INTO public.memberships (tenant_id, user_id, role)
                VALUES (%s, %s, 'owner')
                ON CONFLICT (tenant_id, user_id) DO UPDATE SET role = EXCLUDED.role
                RETURNING tenant_id, role::text
                """,
                (tenant_id, user_id),
            )
            mem = cur.fetchone()
            cur.execute(
                """
                INSERT INTO public.notification_settings (tenant_id)
                VALUES (%s)
                ON CONFLICT (tenant_id) DO NOTHING
                """,
                (tenant_id,),
            )
    return TenantMembership(
        tenant_id=tenant_id,
        role=str(mem[1]),
        tenant_slug=slug,
    )


def get_onboarding_status(tenant_id: UUID) -> TenantOnboarding:
    with psycopg.connect(database_url(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.display_name, t.slug, t.onboarding_completed_at
                FROM public.tenants t
                WHERE t.id = %s
                """,
                (tenant_id,),
            )
            row = cur.fetchone()
            if not row:
                raise LookupError("tenant not found")
            cur.execute(
                """
                SELECT 1 FROM public.connector_credentials
                WHERE tenant_id = %s AND source = 'shopify'
                LIMIT 1
                """,
                (tenant_id,),
            )
            shopify = cur.fetchone() is not None
    return TenantOnboarding(
        tenant_id=row[0],
        display_name=row[1],
        slug=row[2],
        onboarding_complete=row[3] is not None,
        shopify_connected=shopify,
    )


def update_tenant_display_name(tenant_id: UUID, display_name: str) -> None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.tenants SET display_name = %s WHERE id = %s
                """,
                (display_name.strip()[:120], tenant_id),
            )


def complete_tenant_onboarding(tenant_id: UUID) -> None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.tenants
                SET onboarding_completed_at = now()
                WHERE id = %s AND onboarding_completed_at IS NULL
                """,
                (tenant_id,),
            )


def get_primary_membership(user_id: UUID) -> TenantMembership | None:
    """First membership for user (Phase 0 single-tenant pilots)."""
    with psycopg.connect(database_url(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.tenant_id, m.role::text, t.slug
                FROM public.memberships m
                JOIN public.tenants t ON t.id = m.tenant_id
                WHERE m.user_id = %s
                ORDER BY m.created_at
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    tenant_id, role, slug = row
    return TenantMembership(tenant_id=tenant_id, role=role, tenant_slug=slug)


def upsert_connector_credential(
    *,
    tenant_id: UUID,
    source: str,
    access_token_encrypted: str,
    account_ref: str | None = None,
    scopes: str | None = None,
) -> None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.connector_credentials (
                    tenant_id, source, shop_domain, access_token_encrypted, scopes, updated_at
                ) VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, source) DO UPDATE SET
                    shop_domain = EXCLUDED.shop_domain,
                    access_token_encrypted = EXCLUDED.access_token_encrypted,
                    scopes = EXCLUDED.scopes,
                    updated_at = now()
                """,
                (tenant_id, source, account_ref, access_token_encrypted, scopes),
            )


def get_connector_credential(tenant_id: UUID, source: str) -> ConnectorCredential | None:
    from trita_api.crypto import decrypt_token

    with psycopg.connect(database_url(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT shop_domain, access_token_encrypted, scopes
                FROM public.connector_credentials
                WHERE tenant_id = %s AND source = %s
                """,
                (tenant_id, source),
            )
            row = cur.fetchone()
    if not row:
        return None
    account_ref, encrypted, scopes = row
    return ConnectorCredential(
        tenant_id=tenant_id,
        source=source,
        account_ref=account_ref,
        access_token=decrypt_token(encrypted),
        scopes=scopes,
    )


def delete_shopify_credential(tenant_id: UUID) -> bool:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.connector_credentials
                WHERE tenant_id = %s AND source = 'shopify'
                """,
                (tenant_id,),
            )
            return cur.rowcount > 0


def get_shopify_credential(tenant_id: UUID) -> ShopifyCredential | None:
    from trita_api.crypto import decrypt_token

    with psycopg.connect(database_url(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT shop_domain, access_token_encrypted, scopes
                FROM public.connector_credentials
                WHERE tenant_id = %s AND source = 'shopify'
                """,
                (tenant_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    shop_domain, encrypted, scopes = row
    return ShopifyCredential(
        tenant_id=tenant_id,
        shop_domain=shop_domain,
        access_token=decrypt_token(encrypted),
        scopes=scopes,
    )
