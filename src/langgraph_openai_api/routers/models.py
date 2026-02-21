"""Models API router: GET /v1/models endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..graph.registry import GraphRegistry
from ..models.models import ModelListResponse, ModelObject

router = APIRouter()

# Will be set by app factory
_registry: GraphRegistry | None = None


def set_registry(registry: GraphRegistry) -> None:
    global _registry
    _registry = registry


def get_registry() -> GraphRegistry:
    if _registry is None:
        raise RuntimeError("GraphRegistry not initialized")
    return _registry


@router.get("/v1/models")
async def list_models() -> ModelListResponse:
    """List all registered graphs as OpenAI models."""
    registry = get_registry()
    graphs = registry.list_graphs()
    models = [
        ModelObject(id=g["id"], created=g["created_at"])
        for g in graphs
    ]
    return ModelListResponse(data=models)


@router.get("/v1/models/{model}")
async def get_model(model: str) -> ModelObject:
    """Get a specific model (graph) by ID."""
    registry = get_registry()
    if not registry.exists(model):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": f"The model '{model}' does not exist",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            },
        )
    graphs = registry.list_graphs()
    for g in graphs:
        if g["id"] == model:
            return ModelObject(id=g["id"], created=g["created_at"])
    # Should not reach here
    return ModelObject(id=model)
