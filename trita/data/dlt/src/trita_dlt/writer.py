"""Postgres writer with idempotent insert (T-P0-013)."""

from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from trita_dlt.envelope import RawEvent

_RAW_INSERT = """
    INSERT INTO {schema}.{table} (
        tenant_id, source, external_id, entity_type,
        payload, payload_hash, ingested_at, lineage
    ) VALUES (
        %(tenant_id)s::uuid, %(source)s, %(external_id)s, %(entity_type)s,
        %(payload)s::jsonb, %(payload_hash)s, %(ingested_at)s::timestamptz,
        %(lineage)s::jsonb
    )
    ON CONFLICT (tenant_id, source, external_id, entity_type) DO NOTHING
    RETURNING id
"""

RAW_TABLES: dict[str, str] = {
    "shopify": "raw.shopify_events",
    "unicommerce": "raw.unicommerce_events",
    "shiprocket": "raw.shiprocket_events",
    "razorpay": "raw.razorpay_events",
    "csv_hub": "raw.csv_hub_events",
    "delhivery": "raw.delhivery_events",
    "meta_ads": "raw.meta_ads_events",
    "google_ads": "raw.google_ads_events",
}


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for raw writes")
    return url


def write_raw_events(events: list[RawEvent], *, source: str) -> tuple[int, int]:
    """Write idempotent raw envelope rows. Returns (inserted, skipped)."""
    if not events:
        return 0, 0
    qualified = RAW_TABLES.get(source)
    if not qualified:
        raise ValueError(f"No raw table for source {source}")
    schema_name, table_name = qualified.split(".", 1)
    query = sql.SQL(_RAW_INSERT).format(
        schema=sql.Identifier(schema_name),
        table=sql.Identifier(table_name),
    )
    inserted = 0
    skipped = 0
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for event in events:
                row = event.as_row()
                cur.execute(
                    query,
                    {
                        "tenant_id": row["tenant_id"],
                        "source": row["source"],
                        "external_id": row["external_id"],
                        "entity_type": row["entity_type"],
                        "payload": Jsonb(row["payload"]),
                        "payload_hash": row["payload_hash"],
                        "ingested_at": row["ingested_at"],
                        "lineage": Jsonb(row["lineage"]) if row["lineage"] else None,
                    },
                )
                if cur.fetchone():
                    inserted += 1
                else:
                    skipped += 1
    return inserted, skipped


def write_shopify_events(events: list[RawEvent]) -> tuple[int, int]:
    return write_raw_events(events, source="shopify")


def write_csv_hub_events(events: list[RawEvent]) -> tuple[int, int]:
    """Write CSV hub rows; per-event `source` is logical (tally, generic, …)."""
    return write_raw_events(events, source="csv_hub")
