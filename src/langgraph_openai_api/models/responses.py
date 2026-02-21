"""Response models for the Responses API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OutputText(BaseModel):
    """Text content within a message output."""

    type: str = "output_text"
    text: str = ""
    annotations: list[Any] = Field(default_factory=list)


class MessageOutputItem(BaseModel):
    """A message output item."""

    type: str = "message"
    id: str = ""
    status: str = "completed"
    role: str = "assistant"
    content: list[OutputText] = Field(default_factory=list)


class FunctionCallOutputItem(BaseModel):
    """A function call output item."""

    type: str = "function_call"
    id: str = ""
    call_id: str = ""
    name: str = ""
    arguments: str = ""
    status: str = "completed"


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ResponseObject(BaseModel):
    """The main response object returned by POST /v1/responses."""

    id: str = ""
    object: str = "response"
    created_at: int = 0
    status: str = "completed"
    model: str = ""
    output: list[MessageOutputItem | FunctionCallOutputItem] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    metadata: dict[str, str] | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    top_p: float | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    tool_choice: str | dict[str, Any] | None = None
    text: dict[str, Any] | None = Field(default=None)
    previous_response_id: str | None = None
    store: bool = True
    error: dict[str, Any] | None = None
