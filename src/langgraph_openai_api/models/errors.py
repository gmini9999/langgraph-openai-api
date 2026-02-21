"""Error response models."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail matching OpenAI error format."""

    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """Error response wrapper."""

    error: ErrorDetail
