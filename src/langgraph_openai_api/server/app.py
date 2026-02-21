"""FastAPI application factory."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..adapters.base import FileAdapter, VectorStoreAdapter
from ..adapters.memory import InMemoryFileAdapter, InMemoryVectorStoreAdapter
from ..graph.loader import load_graph
from ..graph.registry import GraphRegistry
from ..graph.runner import GraphRunner
from ..models.common import unix_timestamp
from ..routers import files as files_router
from ..routers import models as models_router
from ..routers import responses as responses_router
from ..routers import vector_stores as vs_router
from ..server.dependencies import is_dev_mode, verify_api_key

logger = logging.getLogger("langgraph_openai_api")


def _load_config(config_path: str) -> dict[str, Any]:
    """Load and parse langgraph.json."""
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        return json.load(f)


def create_app(
    config_path: str = "./langgraph.json",
    vector_store_adapter: VectorStoreAdapter | None = None,
    file_adapter: FileAdapter | None = None,
    dev_mode: bool = False,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_path: Path to langgraph.json.
        vector_store_adapter: Optional custom vector store adapter.
        file_adapter: Optional custom file adapter.
        dev_mode: If True, sets OPENLANG_DEV=true.

    Returns:
        Configured FastAPI application.
    """
    import os

    if dev_mode:
        os.environ["OPENLANG_DEV"] = "true"

    # Load config
    config = _load_config(config_path)

    # Load .env file
    env_file = config.get("env", ".env")
    config_dir = str(Path(config_path).resolve().parent)
    env_path = Path(config_dir) / env_file
    if env_path.exists():
        load_dotenv(str(env_path))

    # Create FastAPI app
    docs_url = "/docs" if is_dev_mode() else None
    app = FastAPI(
        title="langgraph-openai-api",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Build graph registry
    registry = GraphRegistry()
    graphs_config = config.get("graphs", {})
    created_at = unix_timestamp()

    for graph_id, module_path in graphs_config.items():
        try:
            graph = load_graph(module_path, base_dir=config_dir)
            registry.register(graph_id, graph, created_at=created_at)
            logger.info(f"Loaded graph: {graph_id} -> {module_path}")
        except Exception as e:
            logger.error(f"Failed to load graph '{graph_id}': {e}")
            raise

    # Build runner
    runner = GraphRunner(registry)

    # Set up adapters (use in-memory defaults if not provided)
    vs_adapter = vector_store_adapter or InMemoryVectorStoreAdapter()
    f_adapter = file_adapter or InMemoryFileAdapter()

    # Wire up routers
    models_router.set_registry(registry)
    responses_router.set_runner(runner)
    vs_router.set_adapter(vs_adapter)
    files_router.set_adapter(f_adapter)

    # Auth dependency for all routers
    auth_deps = [Depends(verify_api_key)]

    app.include_router(models_router.router, dependencies=auth_deps)
    app.include_router(responses_router.router, dependencies=auth_deps)
    app.include_router(vs_router.router, dependencies=auth_deps)
    app.include_router(files_router.router, dependencies=auth_deps)

    # Global exception handler for OpenAI-compatible errors
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": str(exc),
                    "type": "server_error",
                    "param": None,
                    "code": "server_error",
                }
            },
        )

    return app
