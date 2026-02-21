"""Test GET /v1/models endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_models(client):
    resp = await client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"]) >= 1
    model_ids = [m["id"] for m in data["data"]]
    assert "test-echo" in model_ids


@pytest.mark.asyncio
async def test_get_model(client):
    resp = await client.get("/v1/models/test-echo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "test-echo"
    assert data["object"] == "model"
    assert data["owned_by"] == "langgraph-openai-api"


@pytest.mark.asyncio
async def test_get_model_not_found(client):
    resp = await client.get("/v1/models/nonexistent")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "model_not_found"
