"""Files API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response

from ..adapters.base import FileAdapter
from ..models.common import ListResponse
from ..models.files import FileDeleteResponse, FileObject

router = APIRouter()

_adapter: FileAdapter | None = None


def set_adapter(adapter: FileAdapter) -> None:
    global _adapter
    _adapter = adapter


def get_adapter() -> FileAdapter:
    if _adapter is None:
        raise HTTPException(status_code=501, detail="File adapter not configured")
    return _adapter


@router.post("/v1/files")
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = Form(...),
):
    adapter = get_adapter()
    content = await file.read()
    result = await adapter.upload_file(
        file_content=content,
        filename=file.filename or "unknown",
        purpose=purpose,
    )
    return FileObject(**result)


@router.get("/v1/files")
async def list_files(
    purpose: str | None = None,
    limit: int = 10000,
    order: str = "desc",
    after: str | None = None,
):
    adapter = get_adapter()
    result = await adapter.list_files(
        purpose=purpose, limit=limit, order=order, after=after,
    )
    return ListResponse(
        data=[FileObject(**f) for f in result["data"]],
        has_more=result.get("has_more", False),
    )


@router.get("/v1/files/{file_id}")
async def get_file(file_id: str):
    adapter = get_adapter()
    try:
        result = await adapter.get_file(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found")
    return FileObject(**result)


@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str):
    adapter = get_adapter()
    result = await adapter.delete_file(file_id)
    return FileDeleteResponse(**result)


@router.get("/v1/files/{file_id}/content")
async def get_file_content(file_id: str):
    adapter = get_adapter()
    try:
        content = await adapter.get_file_content(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found")
    return Response(content=content, media_type="application/octet-stream")
