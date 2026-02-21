"""Translate OpenAI Responses API requests to LangGraph state."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..models.requests import CreateResponseRequest
from .state_mapper import get_input_mapper


def _convert_content(content: str | list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    """Convert OpenAI content format to LangChain content format."""
    if isinstance(content, str):
        return content

    result = []
    for item in content:
        content_type = item.get("type", "")
        if content_type == "input_text":
            result.append({"type": "text", "text": item.get("text", "")})
        elif content_type == "input_image":
            image_url = item.get("image_url", "")
            if isinstance(image_url, str):
                result.append({"type": "image_url", "image_url": {"url": image_url}})
            else:
                result.append({"type": "image_url", "image_url": image_url})
        else:
            result.append(item)
    return result


def _convert_messages(input_data: str | list[dict[str, Any]]) -> list:
    """Convert OpenAI input to LangChain messages."""
    if isinstance(input_data, str):
        return [HumanMessage(content=input_data)]

    messages = []
    for msg in input_data:
        role = msg.get("role", "user")
        content = _convert_content(msg.get("content", ""))

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role in ("system", "developer"):
            messages.append(SystemMessage(content=content))

    return messages


def translate_input(request: CreateResponseRequest) -> dict[str, Any]:
    """Translate an OpenAI request to LangGraph state.

    If a custom input mapper is registered for the graph ID (request.model),
    it is called with {"messages": [...], "metadata": ..., ...}.
    Otherwise, returns {"messages": [...]}.
    """
    messages = _convert_messages(request.input)

    if request.instructions:
        messages.insert(0, SystemMessage(content=request.instructions))

    custom_mapper = get_input_mapper(request.model)
    if custom_mapper is not None:
        mapper_input: dict[str, Any] = {"messages": messages}
        if request.metadata:
            mapper_input["metadata"] = request.metadata
        if request.temperature is not None:
            mapper_input["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            mapper_input["max_output_tokens"] = request.max_output_tokens
        if request.tools:
            mapper_input["tools"] = request.tools
        return custom_mapper(mapper_input)

    return {"messages": messages}
