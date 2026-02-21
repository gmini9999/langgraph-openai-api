"""Shared fixtures for tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Annotated, Any

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# --- Test graph ---

class TestState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


async def echo_node(state: TestState) -> dict[str, Any]:
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None
    content = last_msg.content if last_msg and hasattr(last_msg, "content") else "(empty)"
    return {"messages": [AIMessage(content=f"Echo: {content}")]}


def build_test_graph():
    builder = StateGraph(TestState)
    builder.add_node("echo", echo_node)
    builder.set_entry_point("echo")
    builder.set_finish_point("echo")
    return builder.compile()


@pytest.fixture
def test_graph():
    return build_test_graph()


@pytest.fixture
def test_graph_file(tmp_path: Path) -> tuple[Path, Path]:
    """Create a temporary graph file and langgraph.json, return (config_path, graph_path)."""
    graph_code = '''
from __future__ import annotations
from typing import Annotated, Any
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

async def echo_node(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None
    content = last_msg.content if last_msg and hasattr(last_msg, "content") else "(empty)"
    return {"messages": [AIMessage(content=f"Echo: {content}")]}

builder = StateGraph(State)
builder.add_node("echo", echo_node)
builder.set_entry_point("echo")
builder.set_finish_point("echo")
graph = builder.compile()
'''
    graph_path = tmp_path / "graph.py"
    graph_path.write_text(graph_code)

    config = {
        "dependencies": ["."],
        "graphs": {
            "test-echo": f"./graph.py:graph"
        },
    }
    config_path = tmp_path / "langgraph.json"
    config_path.write_text(json.dumps(config))

    return config_path, graph_path


@pytest.fixture
def test_app(test_graph_file):
    """Create a test FastAPI app."""
    os.environ["OPENLANG_DEV"] = "true"
    config_path, _ = test_graph_file

    from langgraph_openai_api.server.app import create_app
    app = create_app(config_path=str(config_path), dev_mode=True)
    return app


@pytest.fixture
async def client(test_app):
    """Create an async test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
