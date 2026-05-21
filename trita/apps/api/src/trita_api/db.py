"""Postgres helpers — always filter by tenant_id from JWT."""

from __future__ import annotations

import os
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
