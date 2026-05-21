"""VA-01: tenant_id from JWT only; body/query override rejected."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from trita_api.main import app
from tests.conftest import mint_test_token

client = TestClient(app)


def test_context_requires_auth() -> None:
    response = client.get("/v1/tenant/context")
    assert response.status_code == 401


def test_context_returns_jwt_tenant(auth_token: str) -> None:
    response = client.get(
        "/v1/tenant/context",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "tenant_id" in body
    assert "user_id" in body


def test_probe_rejects_body_tenant_override() -> None:
    jwt_tenant = uuid4()
    other_tenant = uuid4()
    token = mint_test_token(tenant_id=jwt_tenant)
    response = client.post(
        "/v1/tenant/probe",
        headers={"Authorization": f"Bearer {token}"},
        json={"tenant_id": str(other_tenant)},
    )
    assert response.status_code == 403
    assert "JWT" in response.json()["detail"]


def test_probe_accepts_matching_body_tenant() -> None:
    tenant_id = uuid4()
    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/tenant/probe",
        headers={"Authorization": f"Bearer {token}"},
        json={"tenant_id": str(tenant_id)},
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(tenant_id)


def test_probe_accepts_empty_body() -> None:
    tenant_id = uuid4()
    token = mint_test_token(tenant_id=tenant_id)
    response = client.post(
        "/v1/tenant/probe",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200


def test_expired_token_rejected() -> None:
    token = mint_test_token(expired=True)
    response = client.get(
        "/v1/tenant/context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
