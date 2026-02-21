"""Vector Stores API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..adapters.base import VectorStoreAdapter
from ..models.common import ListResponse
from ..models.vector_stores import (
    AddFileToVectorStoreRequest,
    CreateVectorStoreRequest,
    ModifyVectorStoreRequest,
    SearchVectorStoreRequest,
    SearchVectorStoreResponse,
    VectorStoreFileObject,
    VectorStoreObject,
)

router = APIRouter()

_adapter: VectorStoreAdapter | None = None


def set_adapter(adapter: VectorStoreAdapter) -> None:
    global _adapter
    _adapter = adapter


def get_adapter() -> VectorStoreAdapter:
    if _adapter is None:
        raise HTTPException(status_code=501, detail="Vector store adapter not configured")
    return _adapter


@router.post("/v1/vector_stores")
async def create_vector_store(request: CreateVectorStoreRequest):
    adapter = get_adapter()
    result = await adapter.create_vector_store(
        name=request.name,
        file_ids=request.file_ids,
        metadata=request.metadata,
        chunking_strategy=request.chunking_strategy,
        expires_after=request.expires_after,
    )
    return VectorStoreObject(**result)


@router.get("/v1/vector_stores")
async def list_vector_stores(
    limit: int = 20,
    order: str = "desc",
    after: str | None = None,
    before: str | None = None,
):
    adapter = get_adapter()
    result = await adapter.list_vector_stores(
        limit=limit, order=order, after=after, before=before,
    )
    return ListResponse(
        data=[VectorStoreObject(**s) for s in result["data"]],
        first_id=result.get("first_id"),
        last_id=result.get("last_id"),
        has_more=result.get("has_more", False),
    )


@router.get("/v1/vector_stores/{vector_store_id}")
async def get_vector_store(vector_store_id: str):
    adapter = get_adapter()
    try:
        result = await adapter.get_vector_store(vector_store_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vector store '{vector_store_id}' not found")
    return VectorStoreObject(**result)


@router.post("/v1/vector_stores/{vector_store_id}", response_model=VectorStoreObject)
async def modify_vector_store(vector_store_id: str, request: ModifyVectorStoreRequest):
    adapter = get_adapter()
    try:
        result = await adapter.modify_vector_store(
            vector_store_id,
            name=request.name,
            metadata=request.metadata,
            expires_after=request.expires_after,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vector store '{vector_store_id}' not found")
    return VectorStoreObject(**result)


@router.delete("/v1/vector_stores/{vector_store_id}")
async def delete_vector_store(vector_store_id: str):
    adapter = get_adapter()
    return await adapter.delete_vector_store(vector_store_id)


@router.post("/v1/vector_stores/{vector_store_id}/search")
async def search_vector_store(vector_store_id: str, request: SearchVectorStoreRequest):
    adapter = get_adapter()
    try:
        result = await adapter.search_vector_store(
            vector_store_id,
            query=request.query,
            max_num_results=request.max_num_results,
            filters=request.filters,
            ranking_options=request.ranking_options,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vector store '{vector_store_id}' not found")
    return SearchVectorStoreResponse(data=result.get("data", []))


@router.post("/v1/vector_stores/{vector_store_id}/files")
async def add_file_to_vector_store(vector_store_id: str, request: AddFileToVectorStoreRequest):
    adapter = get_adapter()
    try:
        result = await adapter.add_file_to_vector_store(
            vector_store_id,
            file_id=request.file_id,
            chunking_strategy=request.chunking_strategy,
            attributes=request.attributes,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vector store '{vector_store_id}' not found")
    return VectorStoreFileObject(**result)


@router.get("/v1/vector_stores/{vector_store_id}/files")
async def list_vector_store_files(
    vector_store_id: str,
    limit: int = 20,
    order: str = "desc",
    after: str | None = None,
):
    adapter = get_adapter()
    result = await adapter.list_vector_store_files(
        vector_store_id, limit=limit, order=order, after=after,
    )
    return ListResponse(
        data=[VectorStoreFileObject(**f) for f in result["data"]],
        first_id=result.get("first_id"),
        last_id=result.get("last_id"),
        has_more=result.get("has_more", False),
    )


@router.get("/v1/vector_stores/{vector_store_id}/files/{file_id}")
async def get_vector_store_file(vector_store_id: str, file_id: str):
    adapter = get_adapter()
    try:
        result = await adapter.get_vector_store_file(vector_store_id, file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found")
    return VectorStoreFileObject(**result)


@router.delete("/v1/vector_stores/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(vector_store_id: str, file_id: str):
    adapter = get_adapter()
    return await adapter.delete_vector_store_file(vector_store_id, file_id)
