"""A simple echo/chat graph for testing and demonstration."""

from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages


class ChatState:
    """Simple chat state with messages."""
    pass


# Use TypedDict for state definition
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


async def echo_node(state: State) -> dict[str, Any]:
    """Echo back the last user message."""
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None
    if last_msg:
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        response = f"Echo: {content}"
    else:
        response = "Echo: (empty)"
    return {"messages": [AIMessage(content=response)]}


# Build the graph
builder = StateGraph(State)
builder.add_node("echo", echo_node)
builder.set_entry_point("echo")
builder.set_finish_point("echo")
graph = builder.compile()
