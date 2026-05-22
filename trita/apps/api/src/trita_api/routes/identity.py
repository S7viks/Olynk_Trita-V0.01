"""Identity v1 API (F-ID-001, F-ID-002)."""

from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from trita_api.auth import TenantDep, reject_tenant_override
from trita_api.db import database_url

router = APIRouter(prefix="/v1/identity", tags=["identity"])


class AliasBody(BaseModel):
    tenant_id: UUID | None = None
    source: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=256)
    canonical_sku_id: str = Field(min_length=1, max_length=64)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


@router.post("/refresh")
def identity_refresh(ctx: TenantDep) -> dict[str, object]:
    """Rebuild sku_alias + order_bridge for tenant (P-IDENTITY-REFRESH)."""
    try:
        from trita_ontology.refresh import refresh_identity
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="trita-ontology package not installed",
        ) from exc
    with psycopg.connect(database_url(), autocommit=True) as conn:
        return refresh_identity(conn, ctx.tenant_id)


@router.get("/stats")
def identity_stats(ctx: TenantDep) -> dict[str, object]:
    """Resolution + bridge join rates from persisted tables."""
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*) FROM public.sku_alias WHERE tenant_id = %s
                """,
                (ctx.tenant_id,),
            )
            alias_count = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT
                    count(*) AS order_keys,
                    count(*) FILTER (WHERE has_shipment) AS with_shipment,
                    count(*) FILTER (WHERE has_payment) AS with_payment,
                    count(*) FILTER (WHERE has_shipment AND has_payment) AS with_both
                FROM public.order_bridge
                WHERE tenant_id = %s
                """,
                (ctx.tenant_id,),
            )
            br = cur.fetchone()
            cur.execute(
                """
                SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE a.canonical_sku_id IS NOT NULL) AS resolved
                FROM gold.fact_order_line AS l
                LEFT JOIN public.sku_alias AS a
                    ON l.tenant_id = a.tenant_id
                    AND a.source = 'shopify'
                    AND a.external_id = l.variant_id
                WHERE l.tenant_id = %s
                """,
                (ctx.tenant_id,),
            )
            res = cur.fetchone()

    total = int(res[0]) if res else 0
    resolved = int(res[1]) if res else 0
    rate = (resolved / total) if total else 1.0
    order_keys = int(br[0]) if br else 0
    return {
        "tenant_id": str(ctx.tenant_id),
        "alias_count": alias_count,
        "resolution": {
            "total_lines": total,
            "resolved_lines": resolved,
            "resolution_rate": round(rate, 4),
            "meets_va13": rate >= 0.9,
        },
        "bridge": {
            "order_keys": order_keys,
            "with_shipment": int(br[1]) if br else 0,
            "with_payment": int(br[2]) if br else 0,
            "with_both": int(br[3]) if br else 0,
            "full_bridge_rate": round((int(br[3]) / order_keys) if br and order_keys else 0.0, 4),
        },
    }


@router.get("/unresolved")
def identity_unresolved(ctx: TenantDep, limit: int = 50) -> dict[str, object]:
    """Exportable unresolved order lines (F-DEC-BLOCKED-PRE)."""
    cap = min(max(limit, 1), 200)
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT l.order_id, l.line_item_id, l.variant_id, l.sku
                FROM gold.fact_order_line AS l
                LEFT JOIN public.sku_alias AS a
                    ON l.tenant_id = a.tenant_id
                    AND a.source = 'shopify'
                    AND a.external_id = l.variant_id
                WHERE l.tenant_id = %s AND a.canonical_sku_id IS NULL
                ORDER BY l.order_id, l.line_item_id
                LIMIT %s
                """,
                (ctx.tenant_id, cap),
            )
            rows = [
                {
                    "order_id": r[0],
                    "line_item_id": r[1],
                    "variant_id": r[2],
                    "sku": r[3],
                }
                for r in cur.fetchall()
            ]
    return {"tenant_id": str(ctx.tenant_id), "count": len(rows), "lines": rows}


@router.post("/aliases")
def identity_merge_alias(body: AliasBody, ctx: TenantDep) -> dict[str, object]:
    """Manual alias merge (stub API for ops queue)."""
    reject_tenant_override(body.tenant_id, ctx)
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.sku_alias (
                    tenant_id, source, external_id, canonical_sku_id,
                    confidence, merged_by, updated_at
                ) VALUES (%s, %s, %s, %s, %s, 'manual', now())
                ON CONFLICT (tenant_id, source, external_id) DO UPDATE SET
                    canonical_sku_id = EXCLUDED.canonical_sku_id,
                    confidence = EXCLUDED.confidence,
                    merged_by = 'manual',
                    updated_at = now()
                """,
                (
                    ctx.tenant_id,
                    body.source.strip().lower(),
                    body.external_id,
                    body.canonical_sku_id,
                    body.confidence,
                ),
            )
    return {"merged": True, "source": body.source, "external_id": body.external_id}
