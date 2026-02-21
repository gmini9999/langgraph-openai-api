"""App factory for uvicorn to use with reload mode."""

from __future__ import annotations

import os


def app():
    """Create the FastAPI app from environment-configured settings."""
    from ..server.app import create_app

    config_path = os.environ.get("_OPENLANG_CONFIG_PATH", "./langgraph.json")
    dev_mode = os.environ.get("_OPENLANG_DEV_MODE", "false").lower() == "true"

    return create_app(config_path=config_path, dev_mode=dev_mode)
