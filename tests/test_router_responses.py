"""Test POST /v1/responses endpoint (non-streaming)."""

import pytest


@pytest.mark.asyncio
async def test_create_response_string_input(client):
    resp = await client.post(
        "/v1/responses",
        json={"model": "test-echo", "input": "Hello"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["model"] == "test-echo"
    assert data["id"].startswith("resp_")

    # Check output
    assert len(data["output"]) >= 1
    msg = data["output"][0]
    assert msg["type"] == "message"
    assert msg["role"] == "assistant"
    assert "Echo: Hello" in msg["content"][0]["text"]


@pytest.mark.asyncio
async def test_create_response_message_array(client):
    resp = await client.post(
        "/v1/responses",
        json={
            "model": "test-echo",
            "input": [
                {"role": "user", "content": "Hi there"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Echo: Hi there" in data["output"][0]["content"][0]["text"]


@pytest.mark.asyncio
async def test_create_response_model_not_found(client):
    resp = await client.post(
        "/v1/responses",
        json={"model": "nonexistent", "input": "Hello"},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "model_not_found"


@pytest.mark.asyncio
async def test_get_response(client):
    # Create first
    create_resp = await client.post(
        "/v1/responses",
        json={"model": "test-echo", "input": "Hello"},
    )
    resp_id = create_resp.json()["id"]

    # Then retrieve
    get_resp = await client.get(f"/v1/responses/{resp_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == resp_id


@pytest.mark.asyncio
async def test_get_response_not_found(client):
    resp = await client.get("/v1/responses/resp_nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_input_items(client):
    create_resp = await client.post(
        "/v1/responses",
        json={"model": "test-echo", "input": "Hello"},
    )
    resp_id = create_resp.json()["id"]

    items_resp = await client.get(f"/v1/responses/{resp_id}/input_items")
    assert items_resp.status_code == 200
    data = items_resp.json()
    assert data["object"] == "list"


@pytest.mark.asyncio
async def test_cancel_response(client):
    resp = await client.post("/v1/responses/resp_fake/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
