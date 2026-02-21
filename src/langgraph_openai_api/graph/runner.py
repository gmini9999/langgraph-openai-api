"""Graph runner: executes graphs with checkpointing support."""

from __future__ import annotations

import uuid
from typing import Any, AsyncGenerator

from langgraph.checkpoint.memory import MemorySaver

from .registry import GraphRegistry


class GraphRunner:
    """Executes registered graphs with checkpointing and thread management."""

    def __init__(self, registry: GraphRegistry) -> None:
        self.registry = registry
        self.checkpointer = MemorySaver()
        # response_id -> thread_id mapping
        self._response_threads: dict[str, str] = {}

    def _get_or_create_thread_id(self, previous_response_id: str | None = None) -> str:
        """Get existing thread_id from previous_response_id, or create new one."""
        if previous_response_id and previous_response_id in self._response_threads:
            return self._response_threads[previous_response_id]
        return str(uuid.uuid4())

    def _build_config(self, thread_id: str) -> dict[str, Any]:
        """Build a LangGraph config with thread_id."""
        return {"configurable": {"thread_id": thread_id}}

    def store_response_thread(self, response_id: str, thread_id: str) -> None:
        """Store response_id -> thread_id mapping."""
        self._response_threads[response_id] = thread_id

    def get_graph(self, graph_id: str) -> Any:
        """Get a graph by ID, injecting checkpointer if needed."""
        graph = self.registry.get(graph_id)
        if graph is None:
            raise ValueError(f"Graph '{graph_id}' not found")

        # Inject checkpointer if the graph doesn't have one
        if hasattr(graph, "checkpointer") and graph.checkpointer is None:
            graph.checkpointer = self.checkpointer

        return graph

    async def ainvoke(
        self,
        graph_id: str,
        state: dict[str, Any],
        previous_response_id: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Invoke a graph and return (result_state, thread_id)."""
        graph = self.get_graph(graph_id)
        thread_id = self._get_or_create_thread_id(previous_response_id)
        config = self._build_config(thread_id)
        result = await graph.ainvoke(state, config=config)
        return result, thread_id

    def get_stream_params(
        self,
        graph_id: str,
        previous_response_id: str | None = None,
    ) -> tuple[Any, dict[str, Any], str]:
        """Get graph, config, and thread_id for streaming."""
        graph = self.get_graph(graph_id)
        thread_id = self._get_or_create_thread_id(previous_response_id)
        config = self._build_config(thread_id)
        return graph, config, thread_id
