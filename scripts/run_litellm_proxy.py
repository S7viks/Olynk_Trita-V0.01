#!/usr/bin/env python3
"""Start LiteLLM proxy on Windows (asyncio loop) with config.yaml loaded."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _patch_uvicorn_for_windows() -> None:
    """litellm CLI hard-codes loop=uvloop; uvloop is not supported on Windows."""
    if os.name != "nt":
        return
    import uvicorn

    _orig = uvicorn.run

    def _run(*args, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("loop") == "uvloop":
            kwargs["loop"] = "asyncio"
        return _orig(*args, **kwargs)

    uvicorn.run = _run  # type: ignore[method-assign]


def main() -> None:
    litellm_dir = Path(__file__).resolve().parents[1] / "trita" / "services" / "litellm"
    config = Path(os.environ.get("LITELLM_CONFIG_FILE", litellm_dir / "config.yaml"))
    host = os.environ.get("LITELLM_HOST", "127.0.0.1")
    port = os.environ.get("LITELLM_PORT", "4000")

    if not config.is_file():
        raise SystemExit(f"LiteLLM config not found: {config}")

    os.chdir(litellm_dir)
    _patch_uvicorn_for_windows()

    from litellm.proxy.proxy_cli import run_server

    argv = [
        "litellm",
        "--config",
        str(config.name if config.parent == litellm_dir else config),
        "--host",
        host,
        "--port",
        port,
    ]
    run_server.main(args=argv[1:], standalone_mode=False)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
