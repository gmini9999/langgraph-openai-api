"""SSE streaming event models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResponseCreatedEvent(BaseModel):
    """Emitted when a response is created."""

    type: str = "response.created"
    response: dict[str, Any] = Field(default_factory=dict)


class ResponseInProgressEvent(BaseModel):
    """Emitted when response processing starts."""

    type: str = "response.in_progress"
    response: dict[str, Any] = Field(default_factory=dict)


class ResponseCompletedEvent(BaseModel):
    """Emitted when response processing completes."""

    type: str = "response.completed"
    response: dict[str, Any] = Field(default_factory=dict)


class ResponseFailedEvent(BaseModel):
    """Emitted when response processing fails."""

    type: str = "response.failed"
    response: dict[str, Any] = Field(default_factory=dict)


class OutputItemAddedEvent(BaseModel):
    """Emitted when an output item is added."""

    type: str = "response.output_item.added"
    output_index: int = 0
    item: dict[str, Any] = Field(default_factory=dict)


class OutputItemDoneEvent(BaseModel):
    """Emitted when an output item is complete."""

    type: str = "response.output_item.done"
    output_index: int = 0
    item: dict[str, Any] = Field(default_factory=dict)


class ContentPartAddedEvent(BaseModel):
    """Emitted when a content part starts."""

    type: str = "response.content_part.added"
    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    part: dict[str, Any] = Field(default_factory=dict)


class ContentPartDoneEvent(BaseModel):
    """Emitted when a content part is complete."""

    type: str = "response.content_part.done"
    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    part: dict[str, Any] = Field(default_factory=dict)


class OutputTextDeltaEvent(BaseModel):
    """Emitted for each text token chunk."""

    type: str = "response.output_text.delta"
    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    delta: str = ""


class OutputTextDoneEvent(BaseModel):
    """Emitted when full text is complete."""

    type: str = "response.output_text.done"
    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    text: str = ""


class FunctionCallArgsDeltaEvent(BaseModel):
    """Emitted for each function call argument chunk."""

    type: str = "response.function_call_arguments.delta"
    item_id: str = ""
    output_index: int = 0
    delta: str = ""


class FunctionCallArgsDoneEvent(BaseModel):
    """Emitted when function call arguments are complete."""

    type: str = "response.function_call_arguments.done"
    item_id: str = ""
    output_index: int = 0
    arguments: str = ""


class ErrorEvent(BaseModel):
    """Emitted on error during streaming."""

    type: str = "error"
    message: str = ""
    code: str = "server_error"
