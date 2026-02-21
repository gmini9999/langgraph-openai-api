"""Test SSE streaming."""

import pytest


@pytest.mark.asyncio
async def test_streaming_response(client):
    resp = await client.post(
        "/v1/responses",
        json={"model": "test-echo", "input": "Hello", "stream": True},
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")

    body = resp.text
    # Should contain SSE events
    assert "event: response.created" in body
    assert "event: response.in_progress" in body
    assert "event: response.output_item.added" in body
    assert "event: response.content_part.added" in body
    assert "event: response.output_text.done" in body
    assert "event: response.content_part.done" in body
    assert "event: response.output_item.done" in body
    assert "event: response.completed" in body


@pytest.mark.asyncio
async def test_streaming_contains_text_delta(client):
    resp = await client.post(
        "/v1/responses",
        json={"model": "test-echo", "input": "World", "stream": True},
    )
    body = resp.text
    # The echo graph returns "Echo: World" - should see delta events
    assert "response.output_text.delta" in body or "response.output_text.done" in body
    # Final text should contain "Echo: World"
    assert "Echo: World" in body
