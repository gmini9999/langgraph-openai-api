"""Translate LangGraph state to OpenAI Responses API format."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage

from ..models.common import generate_function_call_id, generate_message_id, generate_response_id, unix_timestamp
from ..models.requests import CreateResponseRequest
from ..models.responses import (
    FunctionCallOutputItem,
    MessageOutputItem,
    OutputText,
    ResponseObject,
    Usage,
)
from .state_mapper import get_output_mapper


def _extract_usage(state: dict[str, Any]) -> Usage:
    """Extract usage info from state if available."""
    usage_data = state.get("usage")
    if isinstance(usage_data, dict):
        return Usage(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
    return Usage()


def translate_output(
    state: dict[str, Any],
    request: CreateResponseRequest,
    response_id: str | None = None,
) -> ResponseObject:
    """Translate LangGraph result state to an OpenAI ResponseObject."""
    resp_id = response_id or generate_response_id()
    output: list[MessageOutputItem | FunctionCallOutputItem] = []

    custom_mapper = get_output_mapper(request.model)

    if custom_mapper is not None:
        text = custom_mapper(state)
        msg_item = MessageOutputItem(
            id=generate_message_id(),
            content=[OutputText(text=text)],
        )
        output.append(msg_item)
    else:
        messages = state.get("messages", [])
        last_ai = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                last_ai = msg
                break

        if last_ai is not None:
            # Handle tool calls
            if last_ai.tool_calls:
                for tc in last_ai.tool_calls:
                    args = tc.get("args", {})
                    args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args)
                    fc_item = FunctionCallOutputItem(
                        id=generate_function_call_id(),
                        call_id=tc.get("id") or "",
                        name=tc.get("name", ""),
                        arguments=args_str,
                    )
                    output.append(fc_item)

            # Handle text content
            if last_ai.content:
                content_text = last_ai.content if isinstance(last_ai.content, str) else str(last_ai.content)
                if content_text:
                    msg_item = MessageOutputItem(
                        id=generate_message_id(),
                        content=[OutputText(text=content_text)],
                    )
                    output.append(msg_item)

    usage = _extract_usage(state)

    return ResponseObject(
        id=resp_id,
        created_at=unix_timestamp(),
        status="completed",
        model=request.model,
        output=output,
        usage=usage,
        metadata=request.metadata,
        temperature=request.temperature,
        max_output_tokens=request.max_output_tokens,
        top_p=request.top_p,
        tools=request.tools,
        tool_choice=request.tool_choice,
        text=request.text,
        previous_response_id=request.previous_response_id,
        store=request.store,
    )
