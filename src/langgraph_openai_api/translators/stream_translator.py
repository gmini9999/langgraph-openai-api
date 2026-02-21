"""Translate LangGraph stream to OpenAI SSE events."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk

from ..models.common import generate_function_call_id, generate_message_id, generate_response_id, unix_timestamp
from ..models.requests import CreateResponseRequest


def format_sse(event_type: str, data: dict[str, Any]) -> str:
    """Format an SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_response_obj(
    response_id: str,
    request: CreateResponseRequest,
    status: str = "in_progress",
    output: list | None = None,
    usage: dict | None = None,
    error: dict | None = None,
) -> dict[str, Any]:
    """Build a response object dict for SSE events."""
    obj: dict[str, Any] = {
        "id": response_id,
        "object": "response",
        "created_at": unix_timestamp(),
        "status": status,
        "model": request.model,
        "output": output or [],
        "usage": usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "metadata": request.metadata,
        "temperature": request.temperature,
        "max_output_tokens": request.max_output_tokens,
        "top_p": request.top_p,
        "tools": request.tools,
        "tool_choice": request.tool_choice,
        "text": request.text,
        "previous_response_id": request.previous_response_id,
        "store": request.store,
    }
    if error:
        obj["error"] = error
    return obj


async def stream_response(
    graph: Any,
    state: dict[str, Any],
    config: dict[str, Any],
    request: CreateResponseRequest,
) -> AsyncGenerator[str, None]:
    """Stream LangGraph output as OpenAI SSE events."""
    response_id = generate_response_id()
    message_id = generate_message_id()

    response_obj = _build_response_obj(response_id, request)

    # 1. Response lifecycle: created + in_progress
    yield format_sse("response.created", {"type": "response.created", "response": response_obj})
    yield format_sse("response.in_progress", {"type": "response.in_progress", "response": response_obj})

    # 2. Output item added (message)
    output_item: dict[str, Any] = {
        "type": "message",
        "id": message_id,
        "status": "in_progress",
        "role": "assistant",
        "content": [],
    }
    yield format_sse("response.output_item.added", {
        "type": "response.output_item.added",
        "output_index": 0,
        "item": output_item,
    })

    # 3. Content part added
    content_part = {"type": "output_text", "text": "", "annotations": []}
    yield format_sse("response.content_part.added", {
        "type": "response.content_part.added",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "part": content_part,
    })

    # 4. Stream text deltas
    full_text = ""
    full_tool_calls: dict[int, dict[str, Any]] = {}  # index -> {id, name, arguments}
    current_output_index = 0
    text_started = True
    fc_items: list[dict[str, Any]] = []

    try:
        async for chunk, metadata in graph.astream(state, config=config, stream_mode="messages"):
            if not isinstance(chunk, (AIMessageChunk, AIMessage)):
                continue

            # Handle text content
            if chunk.content and isinstance(chunk.content, str):
                delta = chunk.content
                full_text += delta
                yield format_sse("response.output_text.delta", {
                    "type": "response.output_text.delta",
                    "item_id": message_id,
                    "output_index": 0,
                    "content_index": 0,
                    "delta": delta,
                })

            # Handle tool call chunks
            if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                for tc_chunk in chunk.tool_call_chunks:
                    idx = tc_chunk.get("index", 0)
                    if idx not in full_tool_calls:
                        # New tool call
                        tc_id = tc_chunk.get("id", generate_function_call_id())
                        tc_name = tc_chunk.get("name", "")
                        full_tool_calls[idx] = {"id": tc_id, "name": tc_name, "arguments": ""}

                        fc_item_id = generate_function_call_id()
                        fc_item = {
                            "type": "function_call",
                            "id": fc_item_id,
                            "call_id": tc_id,
                            "name": tc_name,
                            "arguments": "",
                            "status": "in_progress",
                        }
                        fc_items.append(fc_item)

                        current_output_index += 1
                        yield format_sse("response.output_item.added", {
                            "type": "response.output_item.added",
                            "output_index": current_output_index,
                            "item": fc_item,
                        })

                    args_delta = tc_chunk.get("args", "")
                    if args_delta:
                        full_tool_calls[idx]["arguments"] += args_delta
                        yield format_sse("response.function_call_arguments.delta", {
                            "type": "response.function_call_arguments.delta",
                            "item_id": fc_items[idx]["id"] if idx < len(fc_items) else "",
                            "output_index": idx + 1,
                            "delta": args_delta,
                        })

        # 5. Finalize tool calls
        for i, (idx, tc_data) in enumerate(full_tool_calls.items()):
            fc_item = fc_items[i] if i < len(fc_items) else {}
            yield format_sse("response.function_call_arguments.done", {
                "type": "response.function_call_arguments.done",
                "item_id": fc_item.get("id", ""),
                "output_index": i + 1,
                "arguments": tc_data["arguments"],
            })
            fc_item_done = {**fc_item, "status": "completed", "arguments": tc_data["arguments"]}
            yield format_sse("response.output_item.done", {
                "type": "response.output_item.done",
                "output_index": i + 1,
                "item": fc_item_done,
            })

        # 6. Finalize text
        yield format_sse("response.output_text.done", {
            "type": "response.output_text.done",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "text": full_text,
        })
        yield format_sse("response.content_part.done", {
            "type": "response.content_part.done",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "part": {"type": "output_text", "text": full_text, "annotations": []},
        })

        completed_item = {
            **output_item,
            "status": "completed",
            "content": [{"type": "output_text", "text": full_text, "annotations": []}],
        }
        yield format_sse("response.output_item.done", {
            "type": "response.output_item.done",
            "output_index": 0,
            "item": completed_item,
        })

        # 7. Response completed
        all_output = [completed_item]
        for i, fc_item in enumerate(fc_items):
            idx = list(full_tool_calls.keys())[i] if i < len(full_tool_calls) else 0
            tc_data = full_tool_calls.get(idx, {})
            all_output.append({**fc_item, "status": "completed", "arguments": tc_data.get("arguments", "")})

        completed_response = _build_response_obj(
            response_id, request, status="completed", output=all_output,
        )
        yield format_sse("response.completed", {"type": "response.completed", "response": completed_response})

    except Exception as e:
        yield format_sse("error", {
            "type": "error",
            "message": str(e),
            "code": "server_error",
        })
        failed_response = _build_response_obj(
            response_id, request, status="failed",
            error={"type": "server_error", "message": str(e)},
        )
        yield format_sse("response.failed", {"type": "response.failed", "response": failed_response})
