"""T-P0-005 — Render blueprint contract (VA-10 prep)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
RENDER_YAML = REPO / "render.yaml"


def test_render_yaml_exists() -> None:
    assert RENDER_YAML.is_file()


def test_trita_api_service_health_and_start() -> None:
    data = yaml.safe_load(RENDER_YAML.read_text(encoding="utf-8"))
    services = {s["name"]: s for s in data["services"]}
    api = services["trita-api"]
    assert api["type"] == "web"
    assert api["healthCheckPath"] == "/health"
    assert "uvicorn" in api["startCommand"]
    assert api["rootDir"] == "trita/apps/api"


def test_trita_litellm_service_present() -> None:
    data = yaml.safe_load(RENDER_YAML.read_text(encoding="utf-8"))
    names = {s["name"] for s in data["services"]}
    assert "trita-litellm" in names
