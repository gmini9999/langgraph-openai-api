"""Vector store models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FileCounts(BaseModel):
    """File counts within a vector store."""

    in_progress: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    total: int = 0


class VectorStoreObject(BaseModel):
    """A vector store object."""

    id: str = ""
    object: str = "vector_store"
    created_at: int = 0
    name: str = ""
    status: str = "completed"
    file_counts: FileCounts = Field(default_factory=FileCounts)
    usage_bytes: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class CreateVectorStoreRequest(BaseModel):
    """POST /v1/vector_stores request body."""

    name: str | None = None
    file_ids: list[str] | None = None
    metadata: dict[str, str] | None = None
    chunking_strategy: dict[str, Any] | None = None
    expires_after: dict[str, Any] | None = None


class ModifyVectorStoreRequest(BaseModel):
    """POST /v1/vector_stores/{id} request body."""

    name: str | None = None
    metadata: dict[str, str] | None = None
    expires_after: dict[str, Any] | None = None


class SearchVectorStoreRequest(BaseModel):
    """POST /v1/vector_stores/{id}/search request body."""

    query: str
    max_num_results: int = 10
    filters: dict[str, Any] | None = None
    ranking_options: dict[str, Any] | None = None


class AddFileToVectorStoreRequest(BaseModel):
    """POST /v1/vector_stores/{id}/files request body."""

    file_id: str
    chunking_strategy: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None


class VectorStoreFileObject(BaseModel):
    """A vector store file object."""

    id: str = ""
    object: str = "vector_store.file"
    vector_store_id: str = ""
    status: str = "completed"
    created_at: int = 0


class SearchResultItem(BaseModel):
    """A single search result."""

    file_id: str = ""
    filename: str = ""
    score: float = 0.0
    content: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class SearchVectorStoreResponse(BaseModel):
    """POST /v1/vector_stores/{id}/search response."""

    object: str = "vector_store.search_results"
    data: list[SearchResultItem] = Field(default_factory=list)
