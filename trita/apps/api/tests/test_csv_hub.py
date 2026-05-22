"""CSV hub F-CONN-005."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "dlt"
    / "src"
    / "trita_dlt"
    / "fixtures"
    / "tally_unit_cost_yoga_bar.csv"
)


def test_csv_templates_public_shape() -> None:
    token = mint_test_token()
    response = client.get(
        "/v1/csv/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    templates = response.json()["templates"]
    ids = {t["template_id"] for t in templates}
    assert "tpl_tally_stock" in ids


@patch("trita_api.routes.csv.process_csv_upload")
def test_csv_upload_multipart(mock_process: MagicMock, tenant_a_id: UUID) -> None:
    mock_process.return_value = MagicMock(
        upload_id=tenant_a_id,
        logical_source="tally",
        entity_type="unit_cost",
        template_id="tpl_tally_stock",
        status="completed",
        row_count=3,
        valid_count=3,
        quarantine_count=0,
        inserted=3,
        skipped=0,
        idempotent_replay=False,
    )
    token = mint_test_token(tenant_id=tenant_a_id)
    content = FIXTURE.read_bytes()
    response = client.post(
        "/v1/csv/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("tally.csv", BytesIO(content), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["logical_source"] == "tally"
    assert body["valid_count"] == 3
    mock_process.assert_called_once()


@patch("trita_api.csv_hub.ingest.write_csv_hub_events", return_value=(2, 0))
@patch("trita_api.csv_hub.ingest.insert_quarantine_rows")
@patch("trita_api.csv_hub.ingest.upsert_integration_health")
@patch("trita_api.csv_hub.ingest.complete_csv_upload")
@patch("trita_api.csv_hub.ingest.create_csv_upload")
@patch("trita_api.csv_hub.ingest.get_csv_upload_by_hash", return_value=None)
def test_process_tally_fixture(
    mock_get: MagicMock,
    mock_create: MagicMock,
    mock_complete: MagicMock,
    mock_health: MagicMock,
    mock_quarantine: MagicMock,
    mock_write: MagicMock,
    tenant_a_id: UUID,
) -> None:
    from uuid import uuid4

    upload_id = uuid4()
    mock_create.return_value = upload_id

    from trita_api.csv_hub.ingest import process_csv_upload

    result = process_csv_upload(
        tenant_id=tenant_a_id,
        file_name="tally.csv",
        content=FIXTURE.read_bytes(),
    )
    assert result.status == "completed"
    assert result.valid_count == 3
    assert result.quarantine_count == 0
    mock_write.assert_called_once()
    events = mock_write.call_args[0][0]
    assert len(events) == 3
    assert events[0].source == "tally"
    assert events[0].entity_type == "unit_cost"


@patch("trita_api.csv_hub.ingest.write_csv_hub_events", return_value=(1, 0))
@patch("trita_api.csv_hub.ingest.insert_quarantine_rows")
@patch("trita_api.csv_hub.ingest.upsert_integration_health")
@patch("trita_api.csv_hub.ingest.complete_csv_upload")
@patch("trita_api.csv_hub.ingest.create_csv_upload")
@patch("trita_api.csv_hub.ingest.get_csv_upload_by_hash", return_value=None)
def test_process_quarantines_bad_row(
    mock_get: MagicMock,
    mock_create: MagicMock,
    mock_complete: MagicMock,
    mock_health: MagicMock,
    mock_quarantine: MagicMock,
    mock_write: MagicMock,
    tenant_a_id: UUID,
) -> None:
    from uuid import uuid4

    mock_create.return_value = uuid4()
    csv_body = (
        "Stock Item Name,Closing Balance,Rate\n"
        "Good SKU,10,5.00\n"
        ",10,5.00\n"
    ).encode()

    from trita_api.csv_hub.ingest import process_csv_upload

    result = process_csv_upload(
        tenant_id=tenant_a_id,
        file_name="bad.csv",
        content=csv_body,
    )
    assert result.valid_count == 1
    assert result.quarantine_count == 1
    mock_quarantine.assert_called_once()


@patch("trita_api.csv_hub.ingest.write_csv_hub_events", return_value=(3, 0))
@patch("trita_api.csv_hub.ingest.insert_quarantine_rows")
@patch("trita_api.csv_hub.ingest.upsert_integration_health")
@patch("trita_api.csv_hub.ingest.complete_csv_upload")
@patch("trita_api.csv_hub.ingest.create_csv_upload")
@patch("trita_api.csv_hub.ingest.get_csv_upload_by_hash")
def test_csv_idempotent_replay(
    mock_get: MagicMock,
    mock_create: MagicMock,
    mock_complete: MagicMock,
    mock_health: MagicMock,
    mock_quarantine: MagicMock,
    mock_write: MagicMock,
    tenant_a_id: UUID,
) -> None:
    from uuid import uuid4

    upload_id = uuid4()
    mock_create.return_value = upload_id
    content = FIXTURE.read_bytes()

    from trita_api.csv_hub.ingest import process_csv_upload

    first = process_csv_upload(
        tenant_id=tenant_a_id,
        file_name="tally.csv",
        content=content,
    )
    assert first.idempotent_replay is False
    assert mock_write.call_count == 1

    mock_get.return_value = {
        "id": upload_id,
        "logical_source": "tally",
        "entity_type": "unit_cost",
        "template_id": "tpl_tally_stock",
        "status": "completed",
        "row_count": 3,
        "valid_count": 3,
        "quarantine_count": 0,
        "inserted_count": 3,
        "skipped_count": 0,
    }
    second = process_csv_upload(
        tenant_id=tenant_a_id,
        file_name="tally.csv",
        content=content,
    )
    assert second.idempotent_replay is True
    assert second.inserted == 3
    assert mock_write.call_count == 1


@patch("trita_api.routes.csv.get_csv_upload")
def test_csv_upload_status_tenant_isolation(
    mock_get: MagicMock,
    tenant_a_id: UUID,
    tenant_b_id: UUID,
) -> None:
    from uuid import uuid4

    upload_id = uuid4()
    mock_get.side_effect = lambda tenant_id, uid: (
        {"upload_id": str(upload_id), "status": "completed"}
        if tenant_id == tenant_a_id and uid == upload_id
        else None
    )

    token_b = mint_test_token(tenant_id=tenant_b_id)
    response = client.get(
        f"/v1/csv/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404

    token_a = mint_test_token(tenant_id=tenant_a_id)
    response_a = client.get(
        f"/v1/csv/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response_a.status_code == 200
