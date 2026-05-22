"""Persist alias + bridge refresh (DB-backed)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg

from trita_ontology.bridge import BridgeStats, build_order_bridge_rows
from trita_ontology.identity import (
    DimSkuRow,
    build_line_variant_aliases,
    build_shopify_aliases,
    compute_resolution_stats,
    match_external_to_dim,
)


def _dim_sku_rows(cur, tenant_id: UUID) -> list[DimSkuRow]:
    cur.execute(
        """
        SELECT sku_key, shopify_variant_id, sku_code, title
        FROM gold.dim_sku
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    return [
        DimSkuRow(
            sku_key=str(r[0]),
            shopify_variant_id=str(r[1]) if r[1] else None,
            sku_code=str(r[2]) if r[2] else None,
            title=str(r[3]) if r[3] else None,
        )
        for r in cur.fetchall()
    ]


def _unicommerce_skus(cur, tenant_id: UUID) -> list[str]:
    cur.execute(
        """
        SELECT DISTINCT payload ->> 'sku_code'
        FROM raw.unicommerce_events
        WHERE tenant_id = %s AND payload ->> 'sku_code' IS NOT NULL
        """,
        (tenant_id,),
    )
    return [str(r[0]) for r in cur.fetchall() if r[0]]


def _tally_skus(cur, tenant_id: UUID) -> list[str]:
    cur.execute(
        """
        SELECT DISTINCT sku_code
        FROM gold.sku_unit_cost
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    return [str(r[0]) for r in cur.fetchall() if r[0]]


def _order_lines(cur, tenant_id: UUID) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT order_id, line_item_id, variant_id, sku
        FROM gold.fact_order_line
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    cols = ["order_id", "line_item_id", "variant_id", "sku"]
    return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


def _shopify_orders(cur, tenant_id: UUID) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT order_id, order_name
        FROM (
            SELECT DISTINCT ON (tenant_id, order_id)
                tenant_id, order_id, order_name
            FROM staging.stg_shopify_orders
            WHERE tenant_id = %s
            ORDER BY tenant_id, order_id, order_updated_at DESC
        ) o
        """,
        (tenant_id,),
    )
    return [{"order_id": r[0], "order_name": r[1]} for r in cur.fetchall()]


def _shipments(cur, tenant_id: UUID) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT shipment_id, order_id, channel_order_id
        FROM gold.fact_shipment
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    return [
        {"shipment_id": r[0], "order_id": r[1], "channel_order_id": r[2]}
        for r in cur.fetchall()
    ]


def _payouts(cur, tenant_id: UUID) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT settlement_id, payment_id, channel_order_id
        FROM gold.fact_payout
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    return [
        {
            "settlement_id": r[0],
            "payment_id": r[1],
            "channel_order_id": r[2],
        }
        for r in cur.fetchall()
    ]


def upsert_aliases(cur, tenant_id: UUID, aliases: list[dict[str, Any]]) -> int:
    count = 0
    for alias in aliases:
        cur.execute(
            """
            INSERT INTO public.sku_alias (
                tenant_id, source, external_id, canonical_sku_id,
                confidence, merged_by, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (tenant_id, source, external_id) DO UPDATE SET
                canonical_sku_id = EXCLUDED.canonical_sku_id,
                confidence = EXCLUDED.confidence,
                merged_by = EXCLUDED.merged_by,
                updated_at = now()
            """,
            (
                tenant_id,
                alias["source"],
                alias["external_id"],
                alias["canonical_sku_id"],
                alias["confidence"],
                alias["merged_by"],
            ),
        )
        count += 1
    return count


def upsert_bridge(cur, tenant_id: UUID, rows: list[dict[str, Any]]) -> int:
    for row in rows:
        cur.execute(
            """
            INSERT INTO public.order_bridge (
                tenant_id, channel_order_key, shopify_order_id, shopify_order_name,
                shipment_id, payment_id, settlement_id,
                has_shipment, has_payment, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (tenant_id, channel_order_key) DO UPDATE SET
                shopify_order_id = EXCLUDED.shopify_order_id,
                shopify_order_name = EXCLUDED.shopify_order_name,
                shipment_id = EXCLUDED.shipment_id,
                payment_id = EXCLUDED.payment_id,
                settlement_id = EXCLUDED.settlement_id,
                has_shipment = EXCLUDED.has_shipment,
                has_payment = EXCLUDED.has_payment,
                updated_at = now()
            """,
            (
                tenant_id,
                row["channel_order_key"],
                row.get("shopify_order_id"),
                row.get("shopify_order_name"),
                row.get("shipment_id"),
                row.get("payment_id"),
                row.get("settlement_id"),
                bool(row.get("has_shipment")),
                bool(row.get("has_payment")),
            ),
        )
    return len(rows)


def load_alias_index(cur, tenant_id: UUID) -> dict[tuple[str, str], str]:
    cur.execute(
        """
        SELECT source, external_id, canonical_sku_id
        FROM public.sku_alias
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    return {(str(r[0]), str(r[1])): str(r[2]) for r in cur.fetchall()}


def refresh_identity(
    conn: psycopg.Connection,
    tenant_id: UUID,
) -> dict[str, Any]:
    with conn.cursor() as cur:
        dim_rows = _dim_sku_rows(cur, tenant_id)
        lines = _order_lines(cur, tenant_id)
        aliases = build_shopify_aliases(dim_rows)
        existing_keys = {(a["source"], a["external_id"]) for a in aliases}
        aliases.extend(build_line_variant_aliases(tenant_id, lines, existing_keys))

        for sku_code in _unicommerce_skus(cur, tenant_id):
            canonical, conf = match_external_to_dim(sku_code, dim_rows, source="unicommerce")
            if canonical:
                aliases.append(
                    {
                        "source": "unicommerce",
                        "external_id": sku_code,
                        "canonical_sku_id": canonical,
                        "confidence": conf,
                        "merged_by": "auto:sku_code",
                    }
                )

        for sku_name in _tally_skus(cur, tenant_id):
            canonical, conf = match_external_to_dim(sku_name, dim_rows, source="tally")
            if canonical:
                aliases.append(
                    {
                        "source": "tally",
                        "external_id": sku_name,
                        "canonical_sku_id": canonical,
                        "confidence": conf,
                        "merged_by": "auto:title",
                    }
                )

        alias_written = upsert_aliases(cur, tenant_id, aliases)
        alias_index = load_alias_index(cur, tenant_id)
        resolution = compute_resolution_stats(lines, alias_index)

        bridge_rows, bridge_stats = build_order_bridge_rows(
            _shopify_orders(cur, tenant_id),
            _shipments(cur, tenant_id),
            _payouts(cur, tenant_id),
        )
        bridge_written = upsert_bridge(cur, tenant_id, bridge_rows)

    return {
        "tenant_id": str(tenant_id),
        "aliases_upserted": alias_written,
        "bridge_rows": bridge_written,
        "resolution": {
            "total_lines": resolution.total_lines,
            "resolved_lines": resolution.resolved_lines,
            "resolution_rate": round(resolution.resolution_rate, 4),
            "meets_va13": resolution.resolution_rate >= 0.9,
        },
        "bridge": {
            "order_keys": bridge_stats.order_keys,
            "with_shipment": bridge_stats.with_shipment,
            "with_payment": bridge_stats.with_payment,
            "with_both": bridge_stats.with_both,
            "shipment_rate": round(bridge_stats.shipment_rate, 4),
            "payment_rate": round(bridge_stats.payment_rate, 4),
            "full_bridge_rate": round(bridge_stats.full_bridge_rate, 4),
        },
        "unresolved_sample": resolution.unresolved_sample,
    }
