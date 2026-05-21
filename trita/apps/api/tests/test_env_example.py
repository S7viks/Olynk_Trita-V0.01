"""VA-11: .env.example documents required vars; no secret-like values in template."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
ENV_EXAMPLE = REPO_ROOT / ".env.example"

# Canonical names workers and deploy docs expect (see docs/OPEN_SOURCE_STACK.md).
REQUIRED_KEYS = frozenset(
    {
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "NEXT_PUBLIC_API_URL",
        "API_JWT_SECRET",
        "DATABASE_URL",
        "ENVIRONMENT",
        "LITELLM_PROXY_URL",
        "LITELLM_MASTER_KEY",
        "LITELLM_TENANT_TOKEN_BUDGET",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "SHOPIFY_CLIENT_ID",
        "SHOPIFY_CLIENT_SECRET",
        "SHOPIFY_OAUTH_REDIRECT_URI",
        "SHOPIFY_REDIRECT_URI",
        "SHOPIFY_SCOPES",
        "SHOPIFY_WEBHOOK_SECRET",
        "YOGA_BAR_SHOP_DOMAIN",
        "YOGA_BAR_TENANT_ID",
        "CONNECTOR_TOKEN_KEY",
        "NEXT_PUBLIC_WEB_URL",
        "RENDER_HEALTH_URL",
    }
)

# Obvious secret patterns must not appear as example values.
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"^sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"^eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
    re.compile(r"^supabase_[a-zA-Z0-9]{20,}"),
    re.compile(r"^shpss_[a-f0-9]{16,}"),
    re.compile(r"^sb_(secret|publishable)_[A-Za-z0-9_-]{10,}"),
    re.compile(r"^postgresql://[^:]+:[^@]+@"),
)


def _parse_env_example(path: Path) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        variables[key.strip()] = value.strip()
    return variables


@pytest.fixture(scope="module")
def env_vars() -> dict[str, str]:
    assert ENV_EXAMPLE.is_file(), f"missing {ENV_EXAMPLE}"
    return _parse_env_example(ENV_EXAMPLE)


def test_env_example_exists() -> None:
    assert ENV_EXAMPLE.is_file()


def test_env_example_documents_required_keys(env_vars: dict[str, str]) -> None:
    documented = set(env_vars)
    missing = REQUIRED_KEYS - documented
    assert not missing, f".env.example missing keys: {sorted(missing)}"


def test_env_example_values_are_not_real_secrets(env_vars: dict[str, str]) -> None:
    for key, value in env_vars.items():
        if not value:
            continue
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            assert not pattern.match(value), (
                f"{key} in .env.example looks like a real secret; leave empty in template"
            )


def test_env_example_supabase_url_is_placeholder(env_vars: dict[str, str]) -> None:
    url = env_vars.get("NEXT_PUBLIC_SUPABASE_URL", "")
    assert "YOUR_PROJECT_REF" in url, "use placeholder project ref in .env.example, not a live project"
