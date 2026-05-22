"""CSV upload + quarantine persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb

from trita_api.db import database_url


@dataclass(frozen=True)
class QuarantineRow:
    upload_id: UUID
    source: str
    entity_type: str | None
    row_number: int
    error_code: str
    raw_snippet: dict[str, Any] | None


def create_csv_upload(
    *,
    tenant_id: UUID,
    file_hash: str,
    file_name: str,
    logical_source: str,
    entity_type: str | None,
    template_id: str | None,
    mapping_profile: dict[str, str] | None,
    status: str,
) -> UUID:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.csv_upload (
                    tenant_id, file_hash, file_name, logical_source,
                    entity_type, template_id, mapping_profile, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::public.csv_upload_status)
                ON CONFLICT (tenant_id, file_hash) DO UPDATE SET
                    updated_at = now()
                RETURNING id
                """,
                (
                    tenant_id,
                    file_hash,
                    file_name,
                    logical_source,
                    entity_type,
                    template_id,
                    json.dumps(mapping_profile) if mapping_profile else None,
                    status,
                ),
            )
            row = cur.fetchone()
            assert row is not None
            return UUID(str(row[0]))


def complete_csv_upload(
    *,
    upload_id: UUID,
    status: str,
    row_count: int,
    valid_count: int,
    quarantine_count: int,
    inserted_count: int,
    skipped_count: int,
) -> None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.csv_upload SET
                    status = %s::public.csv_upload_status,
                    row_count = %s,
                    valid_count = %s,
                    quarantine_count = %s,
                    inserted_count = %s,
                    skipped_count = %s,
                    updated_at = now()
                WHERE id = %s
                """,
                (
                    status,
                    row_count,
                    valid_count,
                    quarantine_count,
                    inserted_count,
                    skipped_count,
                    upload_id,
                ),
            )


def get_csv_upload_by_hash(tenant_id: UUID, file_hash: str) -> dict[str, Any] | None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, logical_source, entity_type, template_id, status,
                       row_count, valid_count, quarantine_count,
                       inserted_count, skipped_count
                FROM public.csv_upload
                WHERE tenant_id = %s AND file_hash = %s
                """,
                (tenant_id, file_hash),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "logical_source": row[1],
        "entity_type": row[2],
        "template_id": row[3],
        "status": row[4],
        "row_count": row[5],
        "valid_count": row[6],
        "quarantine_count": row[7],
        "inserted_count": row[8],
        "skipped_count": row[9],
    }


def get_csv_upload(tenant_id: UUID, upload_id: UUID) -> dict[str, Any] | None:
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, file_name, logical_source, entity_type, template_id,
                       status, row_count, valid_count, quarantine_count,
                       inserted_count, skipped_count, created_at, updated_at
                FROM public.csv_upload
                WHERE tenant_id = %s AND id = %s
                """,
                (tenant_id, upload_id),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "upload_id": str(row[0]),
        "file_name": row[1],
        "logical_source": row[2],
        "entity_type": row[3],
        "template_id": row[4],
        "status": row[5],
        "row_count": row[6],
        "valid_count": row[7],
        "quarantine_count": row[8],
        "inserted": row[9],
        "skipped": row[10],
        "created_at": row[11].isoformat() if row[11] else None,
        "updated_at": row[12].isoformat() if row[12] else None,
    }


def reset_csv_hub_source(*, tenant_id: UUID, logical_source: str) -> dict[str, int]:
    """Remove CSV hub data for a logical source so the tenant can re-upload."""
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM raw.csv_hub_events
                WHERE tenant_id = %s AND source = %s
                """,
                (tenant_id, logical_source),
            )
            raw_deleted = cur.rowcount
            cur.execute(
                """
                DELETE FROM quarantine.csv_hub
                WHERE tenant_id = %s AND source = %s
                """,
                (tenant_id, logical_source),
            )
            quarantine_deleted = cur.rowcount
            cur.execute(
                """
                DELETE FROM public.csv_upload
                WHERE tenant_id = %s AND logical_source = %s
                """,
                (tenant_id, logical_source),
            )
            uploads_deleted = cur.rowcount
    return {
        "raw_deleted": raw_deleted,
        "quarantine_deleted": quarantine_deleted,
        "uploads_deleted": uploads_deleted,
    }


def insert_quarantine_rows(*, tenant_id: UUID, rows: list[QuarantineRow]) -> None:
    if not rows:
        return
    with psycopg.connect(database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for q in rows:
                cur.execute(
                    """
                    INSERT INTO quarantine.csv_hub (
                        tenant_id, upload_id, source, entity_type,
                        row_number, error_code, raw_snippet
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        tenant_id,
                        q.upload_id,
                        q.source,
                        q.entity_type,
                        q.row_number,
                        q.error_code,
                        Jsonb(q.raw_snippet) if q.raw_snippet else None,
                    ),
                )
