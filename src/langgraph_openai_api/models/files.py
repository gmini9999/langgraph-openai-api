"""File API models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileObject(BaseModel):
    """A file object."""

    id: str = ""
    object: str = "file"
    bytes: int = 0
    created_at: int = 0
    filename: str = ""
    purpose: str = ""


class FileListResponse(BaseModel):
    """GET /v1/files response."""

    object: str = "list"
    data: list[FileObject] = Field(default_factory=list)
    has_more: bool = False


class FileDeleteResponse(BaseModel):
    """DELETE /v1/files/{file_id} response."""

    id: str = ""
    object: str = "file"
    deleted: bool = True
