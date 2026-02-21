"""Responses API router: POST /v1/responses and related endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..graph.runner import GraphRunner
from ..models.requests import CreateResponseRequest
from ..translators.input_translator import translate_input
from ..translators.output_translator import translate_output
from ..translators.stream_translator import stream_response

router = APIRouter()

# Will be set by app factory
_runner: GraphRunner | None = None
_response_store: dict[str, dict[str, Any]] = {}
_input_store: dict[str, Any] = {}


def set_runner(runner: GraphRunner) -> None:
    global _runner
    _runner = runner


def get_runner() -> GraphRunner:
    if _runner is None:
        raise RuntimeError("GraphRunner not initialized")
    return _runner


@router.post("/v1/responses")
async def create_response(request: CreateResponseRequest):
    """Create a response by executing a graph."""
    runner = get_runner()

    # 1. Check graph exists
    if not runner.registry.exists(request.model):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": f"The model '{request.model}' does not exist",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            },
        )

    # 2. Translate input
    state = translate_input(request)

    # 3. Stream or invoke
    if request.stream:
        graph, config, thread_id = runner.get_stream_params(
            request.model,
            previous_response_id=request.previous_response_id,
        )

        async def _stream_wrapper():
            response_id = None
            async for event in stream_response(graph, state, config, request):
                # Extract response_id from first event for thread mapping
                if response_id is None:
                    import json as _json
                    try:
                        lines = event.split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                data = _json.loads(line[6:])
                                resp = data.get("response", {})
                                if resp.get("id"):
                                    response_id = resp["id"]
                                    runner.store_response_thread(response_id, thread_id)
                                break
                    except Exception:
                        pass
                yield event

        return StreamingResponse(
            _stream_wrapper(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # Non-streaming
    try:
        result_state, thread_id = await runner.ainvoke(
            request.model,
            state,
            previous_response_id=request.previous_response_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "param": None,
                    "code": "server_error",
                }
            },
        )

    response = translate_output(result_state, request)
    runner.store_response_thread(response.id, thread_id)

    # Store for later retrieval
    _response_store[response.id] = response.model_dump()
    _input_store[response.id] = request.model_dump()

    return response


@router.get("/v1/responses/{response_id}")
async def get_response(response_id: str):
    """Retrieve a previously created response."""
    if response_id not in _response_store:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": f"Response '{response_id}' not found",
                    "type": "not_found_error",
                    "param": "response_id",
                    "code": "not_found",
                }
            },
        )
    return _response_store[response_id]


@router.get("/v1/responses/{response_id}/input_items")
async def get_input_items(response_id: str):
    """Retrieve input items for a response."""
    if response_id not in _input_store:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": f"Response '{response_id}' not found",
                    "type": "not_found_error",
                    "param": "response_id",
                    "code": "not_found",
                }
            },
        )
    req_data = _input_store[response_id]
    input_data = req_data.get("input", [])
    if isinstance(input_data, str):
        items = [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": input_data}]}]
    else:
        items = [{"type": "message", **item} for item in input_data]
    return {"object": "list", "data": items}


@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(response_id: str):
    """Cancel a response (best-effort)."""
    if response_id in _response_store:
        _response_store[response_id]["status"] = "cancelled"
    return {"id": response_id, "status": "cancelled"}
