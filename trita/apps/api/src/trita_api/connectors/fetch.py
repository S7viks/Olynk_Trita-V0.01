"""Fetch connector payloads — live API when creds exist, else dev fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
import trita_dlt

from trita_api.connectors.registry import ConnectorSpec
from trita_api.db import ConnectorCredential

_FIXTURE_DIR = Path(trita_dlt.__file__).resolve().parent / "fixtures"
_FIXTURE_FILES = {
    "unicommerce": "unicommerce_yoga_bar.json",
    "shiprocket": "shiprocket_yoga_bar.json",
    "razorpay": "razorpay_yoga_bar.json",
    "delhivery": "delhivery_yoga_bar.json",
    "meta_ads": "meta_ads_yoga_bar.json",
    "google_ads": "google_ads_yoga_bar.json",
}


def _use_dev_fixtures() -> bool:
    return os.environ.get("CONNECTOR_DEV_FIXTURES", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _load_fixture(source: str) -> list[dict[str, Any]]:
    path = _FIXTURE_DIR / _FIXTURE_FILES[source]
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_secret(cred: ConnectorCredential) -> dict[str, str]:
    try:
        parsed = json.loads(cred.access_token)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass
    return {"api_key": cred.access_token}


def fetch_unicommerce_inventory(cred: ConnectorCredential) -> list[dict[str, Any]]:
    secrets = _parse_secret(cred)
    base = secrets.get("base_url") or os.environ.get("UNICOMMERCE_BASE_URL", "").strip()
    token = secrets.get("access_token") or secrets.get("api_key", "")
    if base and token:
        url = f"{base.rstrip('/')}/services/rest/v1/inventory/inventorySnapshot"
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            body = resp.json()
            items = body.get("inventorySnapshots") or body.get("items") or body
            if isinstance(items, list):
                return items
    if _use_dev_fixtures():
        return _load_fixture("unicommerce")
    raise RuntimeError("Unicommerce credentials or CONNECTOR_DEV_FIXTURES required")


def fetch_shiprocket_shipments(cred: ConnectorCredential) -> list[dict[str, Any]]:
    secrets = _parse_secret(cred)
    email = secrets.get("email") or os.environ.get("SHIPROCKET_EMAIL", "")
    password = secrets.get("password") or os.environ.get("SHIPROCKET_PASSWORD", "")
    token = secrets.get("access_token", "")
    if not token and email and password:
        with httpx.Client(timeout=60.0) as client:
            auth = client.post(
                "https://apiv2.shiprocket.in/v1/external/auth/login",
                json={"email": email, "password": password},
            )
            auth.raise_for_status()
            token = str(auth.json().get("token", ""))
    if token:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(
                "https://apiv2.shiprocket.in/v1/external/orders",
                headers={"Authorization": f"Bearer {token}"},
                params={"page": 1, "per_page": 50},
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data") or data.get("orders") or []
            if isinstance(items, list):
                return items
    if _use_dev_fixtures():
        return _load_fixture("shiprocket")
    raise RuntimeError("Shiprocket credentials or CONNECTOR_DEV_FIXTURES required")


def fetch_razorpay_settlements(cred: ConnectorCredential) -> list[dict[str, Any]]:
    secrets = _parse_secret(cred)
    key_id = secrets.get("key_id") or secrets.get("api_key") or os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = secrets.get("key_secret") or secrets.get("api_secret") or os.environ.get(
        "RAZORPAY_KEY_SECRET", ""
    )
    if key_id and key_secret:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(
                "https://api.razorpay.com/v1/settlements",
                auth=(key_id, key_secret),
                params={"count": 50},
            )
            resp.raise_for_status()
            items = resp.json().get("items") or []
            if isinstance(items, list):
                return items
    if _use_dev_fixtures():
        return _load_fixture("razorpay")
    raise RuntimeError("Razorpay credentials or CONNECTOR_DEV_FIXTURES required")


def _beta_fixture_fetch(source: str, cred: ConnectorCredential) -> list[dict[str, Any]]:
    """RM-3 beta connectors: fixture ingest until live API URLs are configured."""
    secrets = _parse_secret(cred)
    if _use_dev_fixtures() or secrets.get("mode") == "fixture" or secrets.get("api_key"):
        return _load_fixture(source)
    raise RuntimeError(f"{source} credentials or CONNECTOR_DEV_FIXTURES required")


def fetch_delhivery_shipments(cred: ConnectorCredential) -> list[dict[str, Any]]:
    return _beta_fixture_fetch("delhivery", cred)


def fetch_meta_ads_daily(cred: ConnectorCredential) -> list[dict[str, Any]]:
    return _beta_fixture_fetch("meta_ads", cred)


def fetch_google_ads_daily(cred: ConnectorCredential) -> list[dict[str, Any]]:
    return _beta_fixture_fetch("google_ads", cred)


def fetch_for_connector(
    spec: ConnectorSpec, cred: ConnectorCredential
) -> list[dict[str, Any]]:
    if spec.source == "unicommerce":
        return fetch_unicommerce_inventory(cred)
    if spec.source == "shiprocket":
        return fetch_shiprocket_shipments(cred)
    if spec.source == "razorpay":
        return fetch_razorpay_settlements(cred)
    if spec.source == "delhivery":
        return fetch_delhivery_shipments(cred)
    if spec.source == "meta_ads":
        return fetch_meta_ads_daily(cred)
    if spec.source == "google_ads":
        return fetch_google_ads_daily(cred)
    raise ValueError(f"Fetch not implemented for {spec.source}")
