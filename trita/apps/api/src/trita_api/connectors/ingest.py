"""Sync RM-1 connectors → raw tables."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from trita_api.connectors.fetch import fetch_for_connector
from trita_api.connectors.normalize import normalize
from trita_api.connectors.registry import ConnectorSpec, get_spec
from trita_api.db import ConnectorCredential
from trita_dlt.writer import write_raw_events


def sync_connector(
    *,
    tenant_id: UUID,
    spec: ConnectorSpec,
    cred: ConnectorCredential,
) -> dict[str, Any]:
    records = fetch_for_connector(spec, cred)
    import json

    try:
        parsed = json.loads(cred.access_token)
        fixture_mode = isinstance(parsed, dict) and parsed.get("mode") == "fixture"
    except json.JSONDecodeError:
        fixture_mode = False
    account_ref = cred.account_ref or "default"
    events = normalize(
        spec.source,
        tenant_id,
        records,
        account_ref=account_ref,
        fixture=fixture_mode,
    )
    inserted, skipped = write_raw_events(events, source=spec.source)
    ingest_mode = "fixture" if fixture_mode else "api"
    return {
        "source": spec.source,
        "events": len(events),
        "inserted": inserted,
        "skipped": skipped,
        "account_ref": account_ref,
        "ingest_mode": ingest_mode,
    }


def sync_source(*, tenant_id: UUID, source: str, cred: ConnectorCredential) -> dict[str, Any]:
    spec = get_spec(source)
    if spec.mode != "api":
        raise ValueError(f"Source {source} is not API-syncable")
    return sync_connector(tenant_id=tenant_id, spec=spec, cred=cred)
