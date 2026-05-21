"""Auth exchange — Supabase user JWT → tenant-scoped API token."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from trita_api.db import TenantMembership
from trita_api.main import app
from uuid import UUID

from tests.conftest import mint_test_token

client = TestClient(app)


def test_auth_exchange_maps_membership(tenant_a_id: UUID, user_a_id: UUID) -> None:
    user_token = mint_test_token(user_id=user_a_id, tenant_id=tenant_a_id)
    membership = TenantMembership(
        tenant_id=tenant_a_id,
        role="owner",
        tenant_slug="yoga-bar",
    )
    with patch("trita_api.routes.auth.get_primary_membership", return_value=membership):
        response = client.post(
            "/v1/auth/exchange",
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == str(tenant_a_id)
    assert body["tenant_slug"] == "yoga-bar"
    assert body["access_token"]


def test_auth_exchange_no_membership() -> None:
    user_id = uuid4()
    user_token = mint_test_token(user_id=user_id, tenant_id=uuid4())
    with patch("trita_api.routes.auth.get_primary_membership", return_value=None):
        response = client.post(
            "/v1/auth/exchange",
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert response.status_code == 403
