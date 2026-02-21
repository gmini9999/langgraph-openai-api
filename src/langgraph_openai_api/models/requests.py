"""Request models for the Responses API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateResponseRequest(BaseModel):
    """POST /v1/responses request body."""

    model: str
    input: str | list[dict[str, Any]]
    stream: bool = False
    instructions: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_output_tokens: int | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    tool_choice: str | dict[str, Any] | None = None
    metadata: dict[str, str] | None = None
    previous_response_id: str | None = None
    store: bool = True
    text: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None
