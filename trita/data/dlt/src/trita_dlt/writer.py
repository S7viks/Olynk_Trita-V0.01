"""Postgres writer with idempotent insert (T-P0-013)."""

from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from trita_dlt.envelope import RawEvent

INSERT_SHOPIFY = sql.SQL("""
    INSERT INTO raw.shopify_events (
        tenant_id, source, external_id, entity_type,
        payload, payload_hash, ingested_at, lineage
    ) VALUES (
        %(tenant_id)s::uuid, %(source)s, %(external_id)s, %(entity_type)s,
        %(payload)s::jsonb, %(payload_hash)s, %(ingested_at)s::timestamptz,
        %(lineage)s::jsonb
    )
    ON CONFLICT (tenant_id, source, external_id, entity_type) DO NOTHING
    RETURNING id
""")


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for raw writes")
    return url


def write_shopify_events(events: list[RawEvent]) -> tuple[int, int]:
    """Returns (inserted_count, skipped_count)."""
    if not events:
        return 0, 0
    inserted = 0
    skipped = 0
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for event in events:
                row = event.as_row()
                cur.execute(
                    INSERT_SHOPIFY,
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
