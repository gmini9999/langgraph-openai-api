"""Models API response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelObject(BaseModel):
    """A model object representing a registered graph."""

    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "langgraph-openai-api"


class ModelListResponse(BaseModel):
    """GET /v1/models response."""

    object: str = "list"
    data: list[ModelObject] = Field(default_factory=list)
