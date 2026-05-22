"""Parse CSV → validate → raw + quarantine."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from trita_dlt.envelope import RawEvent
from trita_dlt.writer import write_csv_hub_events

from trita_api.csv_hub.db import (
    QuarantineRow,
    complete_csv_upload,
    create_csv_upload,
    get_csv_upload_by_hash,
    insert_quarantine_rows,
)
from trita_api.csv_hub.templates import (
    TEMPLATES,
    build_column_map_from_template,
    detect_template,
)
from trita_api.csv_hub.validate import validate_canonical_row
from trita_api.integration_health import upsert_integration_health


@dataclass(frozen=True)
class UploadResult:
    upload_id: UUID
    logical_source: str
    entity_type: str
    template_id: str | None
    status: str
    row_count: int
    valid_count: int
    quarantine_count: int
    inserted: int
    skipped: int
    idempotent_replay: bool


def _file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _row_external_id(
    *,
    tenant_id: UUID,
    source: str,
    entity_type: str,
    canonical: dict[str, Any],
    row_number: int,
) -> str:
    fingerprint = json.dumps(
        {"tenant": str(tenant_id), "source": source, "entity": entity_type, **canonical},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(f"{fingerprint}|{row_number}".encode()).hexdigest()[:32]


def _map_row(raw_row: dict[str, str], column_map: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for canonical, source_col in column_map.items():
        if source_col in raw_row:
            out[canonical] = raw_row[source_col]
    return out


def process_csv_upload(
    *,
    tenant_id: UUID,
    file_name: str,
    content: bytes,
    logical_source: str | None = None,
    entity_type: str | None = None,
    template_id: str | None = None,
    column_map: dict[str, str] | None = None,
) -> UploadResult:
    file_hash = _file_hash(content)
    existing = get_csv_upload_by_hash(tenant_id, file_hash)
    if existing and existing["status"] == "completed":
        return UploadResult(
            upload_id=UUID(str(existing["id"])),
            logical_source=existing["logical_source"],
            entity_type=existing["entity_type"] or "",
            template_id=existing.get("template_id"),
            status="completed",
            row_count=existing["row_count"],
            valid_count=existing["valid_count"],
            quarantine_count=existing["quarantine_count"],
            inserted=existing["inserted_count"],
            skipped=existing["skipped_count"],
            idempotent_replay=True,
        )

    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        upload_id = create_csv_upload(
            tenant_id=tenant_id,
            file_hash=file_hash,
            file_name=file_name,
            logical_source=logical_source or "generic",
            entity_type=entity_type,
            template_id=template_id,
            mapping_profile=column_map,
            status="failed",
        )
        _update_health_failed(tenant_id, logical_source or "generic", "No CSV headers")
        return UploadResult(
            upload_id=upload_id,
            logical_source=logical_source or "generic",
            entity_type=entity_type or "",
            template_id=template_id,
            status="failed",
            row_count=0,
            valid_count=0,
            quarantine_count=0,
            inserted=0,
            skipped=0,
            idempotent_replay=False,
        )

    headers = list(reader.fieldnames)
    tpl = TEMPLATES.get(template_id) if template_id else detect_template(headers)
    if tpl:
        column_map = build_column_map_from_template(tpl, headers)
        logical_source = logical_source or tpl.logical_source
        entity_type = entity_type or tpl.entity_type
        template_id = tpl.template_id
    elif not column_map or not entity_type:
        upload_id = create_csv_upload(
            tenant_id=tenant_id,
            file_hash=file_hash,
            file_name=file_name,
            logical_source=logical_source or "generic",
            entity_type=entity_type,
            template_id=template_id,
            mapping_profile=column_map,
            status="failed",
        )
        _update_health_failed(
            tenant_id,
            logical_source or "generic",
            "Unknown format — provide template_id or column_map + entity_type",
        )
        return UploadResult(
            upload_id=upload_id,
            logical_source=logical_source or "generic",
            entity_type=entity_type or "",
            template_id=template_id,
            status="failed",
            row_count=0,
            valid_count=0,
            quarantine_count=0,
            inserted=0,
            skipped=0,
            idempotent_replay=False,
        )

    logical_source = logical_source or "generic"
    entity_type = entity_type or "order_line"
    upload_id = create_csv_upload(
        tenant_id=tenant_id,
        file_hash=file_hash,
        file_name=file_name,
        logical_source=logical_source,
        entity_type=entity_type,
        template_id=template_id,
        mapping_profile=column_map,
        status="processing",
    )

    events: list[RawEvent] = []
    quarantine: list[QuarantineRow] = []
    row_count = 0
    valid_count = 0

    for row_number, raw_row in enumerate(reader, start=2):
        if not any(str(v).strip() for v in raw_row.values()):
            continue
        row_count += 1
        mapped = _map_row(raw_row, column_map)
        canonical, err = validate_canonical_row(entity_type, mapped)
        if err:
            quarantine.append(
                QuarantineRow(
                    upload_id=upload_id,
                    source=logical_source,
                    entity_type=entity_type,
                    row_number=row_number,
                    error_code=err,
                    raw_snippet=dict(raw_row),
                )
            )
            continue
        valid_count += 1
        ext_id = _row_external_id(
            tenant_id=tenant_id,
            source=logical_source,
            entity_type=entity_type,
            canonical=canonical,
            row_number=row_number,
        )
        events.append(
            RawEvent(
                tenant_id=tenant_id,
                source=logical_source,
                external_id=ext_id,
                entity_type=entity_type,
                payload=canonical,
                lineage={
                    "upload_id": str(upload_id),
                    "file_name": file_name,
                    "template_id": template_id,
                    "row_number": row_number,
                    "mapping_profile": column_map,
                },
            )
        )

    inserted, skipped = write_csv_hub_events(events) if events else (0, 0)
    if quarantine:
        insert_quarantine_rows(tenant_id=tenant_id, rows=quarantine)

    if row_count == 0:
        status = "failed"
        health_status = "failed"
        message = "CSV has no data rows"
    elif valid_count == 0:
        status = "failed"
        health_status = "failed"
        message = "All rows quarantined"
    elif quarantine:
        status = "completed"
        health_status = "degraded"
        message = f"{len(quarantine)} rows quarantined"
    else:
        status = "completed"
        health_status = "healthy"
        message = "Upload validated"

    complete_csv_upload(
        upload_id=upload_id,
        status=status,
        row_count=row_count,
        valid_count=valid_count,
        quarantine_count=len(quarantine),
        inserted_count=inserted,
        skipped_count=skipped,
    )

    health_source = "tally" if logical_source == "tally" else logical_source
    upsert_integration_health(
        tenant_id=tenant_id,
        source=health_source,
        status=health_status,
        last_sync_at=datetime.now(UTC),
        detail={
            "connected": True,
            "upload_id": str(upload_id),
            "file_name": file_name,
            "template_id": template_id,
            "row_count": row_count,
            "valid_count": valid_count,
            "quarantine_count": len(quarantine),
            "inserted": inserted,
            "skipped": skipped,
            "message": message,
            "mode": "csv_hub",
        },
        freshness_sla_hours=168 if health_source == "tally" else 24,
    )

    return UploadResult(
        upload_id=upload_id,
        logical_source=logical_source,
        entity_type=entity_type,
        template_id=template_id,
        status=status,
        row_count=row_count,
        valid_count=valid_count,
        quarantine_count=len(quarantine),
        inserted=inserted,
        skipped=skipped,
        idempotent_replay=False,
    )


def _update_health_failed(tenant_id: UUID, source: str, message: str) -> None:
    health_source = "tally" if source == "tally" else source
    upsert_integration_health(
        tenant_id=tenant_id,
        source=health_source,
        status="failed",
        detail={"connected": False, "message": message, "mode": "csv_hub"},
        freshness_sla_hours=168 if health_source == "tally" else 24,
    )
