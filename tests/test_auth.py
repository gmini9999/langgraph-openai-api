"""Test authentication behavior."""

import os

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_dev_mode_no_auth_required(client):
    """In dev mode, requests without auth should work."""
    resp = await client.get("/v1/models")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_serve_mode_requires_auth(test_graph_file):
    """In serve mode, requests without auth should fail."""
    config_path, _ = test_graph_file

    # Remove dev mode, set API key
    os.environ.pop("OPENLANG_DEV", None)
    os.environ["OPENLANG_API_KEY"] = "sk-test-key-12345"

    from langgraph_openai_api.server.app import create_app
    app = create_app(config_path=str(config_path), dev_mode=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Without auth header
        resp = await ac.get("/v1/models")
        assert resp.status_code == 401 or resp.status_code == 403

        # With correct auth header
        resp = await ac.get(
            "/v1/models",
            headers={"Authorization": "Bearer sk-test-key-12345"},
        )
        assert resp.status_code == 200

        # With wrong auth header
        resp = await ac.get(
            "/v1/models",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401

    # Clean up
    os.environ["OPENLANG_DEV"] = "true"
    os.environ.pop("OPENLANG_API_KEY", None)


@pytest.mark.asyncio
async def test_multiple_api_keys(test_graph_file):
    """Multiple API keys should all be accepted."""
    config_path, _ = test_graph_file

    os.environ.pop("OPENLANG_DEV", None)
    os.environ["OPENLANG_API_KEY"] = "sk-key-1,sk-key-2,sk-key-3"

    from langgraph_openai_api.server.app import create_app
    app = create_app(config_path=str(config_path), dev_mode=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for key in ["sk-key-1", "sk-key-2", "sk-key-3"]:
            resp = await ac.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            assert resp.status_code == 200, f"Key {key} should be accepted"

    os.environ["OPENLANG_DEV"] = "true"
    os.environ.pop("OPENLANG_API_KEY", None)
