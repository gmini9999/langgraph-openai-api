"""Graph registry: maps graph_id to compiled graph instances."""

from __future__ import annotations

from typing import Any


class GraphRegistry:
    """Registry mapping graph IDs to compiled LangGraph instances."""

    def __init__(self) -> None:
        self._graphs: dict[str, Any] = {}
        self._created_at: dict[str, int] = {}

    def register(self, graph_id: str, graph: Any, created_at: int = 0) -> None:
        """Register a graph instance under a graph ID."""
        self._graphs[graph_id] = graph
        self._created_at[graph_id] = created_at

    def get(self, graph_id: str) -> Any | None:
        """Get a graph by ID, or None if not found."""
        return self._graphs.get(graph_id)

    def exists(self, graph_id: str) -> bool:
        """Check if a graph ID is registered."""
        return graph_id in self._graphs

    def list_graphs(self) -> list[dict[str, Any]]:
        """List all registered graphs as dicts with id and created_at."""
        return [
            {"id": gid, "created_at": self._created_at.get(gid, 0)}
            for gid in self._graphs
        ]

    def graph_ids(self) -> list[str]:
        """Return all registered graph IDs."""
        return list(self._graphs.keys())
