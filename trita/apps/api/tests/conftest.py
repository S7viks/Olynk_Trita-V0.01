from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import jwt
import pytest

TEST_JWT_SECRET = "test-jwt-secret-for-isolation-suite-only"

DLT_SRC = Path(__file__).resolve().parents[3] / "data" / "dlt" / "src"
if str(DLT_SRC) not in sys.path:
    sys.path.insert(0, str(DLT_SRC))

ONTOLOGY_SRC = Path(__file__).resolve().parents[3] / "packages" / "ontology" / "src"
if str(ONTOLOGY_SRC) not in sys.path:
    sys.path.insert(0, str(ONTOLOGY_SRC))

DECISIONS_SRC = Path(__file__).resolve().parents[3] / "packages" / "decisions" / "src"
if str(DECISIONS_SRC) not in sys.path:
    sys.path.insert(0, str(DECISIONS_SRC))


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("CONNECTOR_TOKEN_KEY", "test-connector-key-32bytes-minimum!!")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv(
        "SHOPIFY_OAUTH_REDIRECT_URI",
        "http://localhost:8000/v1/sources/shopify/callback",
    )
    monkeypatch.setenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")


def mint_test_token(
    *,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    role: str = "owner",
    expired: bool = False,
) -> str:
    user_id = user_id or uuid4()
    tenant_id = tenant_id or uuid4()
    exp = datetime.now(UTC) + (timedelta(hours=-1) if expired else timedelta(hours=1))
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "aud": "authenticated",
        "exp": exp,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def tenant_a_id() -> UUID:
    return UUID("11111111-1111-1111-1111-111111111101")


@pytest.fixture
def tenant_b_id() -> UUID:
    return UUID("22222222-2222-2222-2222-222222222202")


@pytest.fixture
def user_a_id() -> UUID:
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def user_b_id() -> UUID:
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def auth_token() -> str:
    return mint_test_token()
