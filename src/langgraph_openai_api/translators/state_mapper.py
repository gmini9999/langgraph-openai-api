"""Custom State mapper registry.

Allows graph modules to register custom input/output mappers per graph ID.
"""

from __future__ import annotations

from typing import Any, Callable

# Global registries: graph_id -> mapper function
_input_mappers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
_output_mappers: dict[str, Callable[[dict[str, Any]], str]] = {}


def register_input_mapper(graph_id: str, fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    """Register a custom input mapper for a graph ID."""
    _input_mappers[graph_id] = fn


def register_output_mapper(graph_id: str, fn: Callable[[dict[str, Any]], str]) -> None:
    """Register a custom output mapper for a graph ID."""
    _output_mappers[graph_id] = fn


def get_input_mapper(graph_id: str) -> Callable[[dict[str, Any]], dict[str, Any]] | None:
    """Get the custom input mapper for a graph ID, or None."""
    return _input_mappers.get(graph_id)


def get_output_mapper(graph_id: str) -> Callable[[dict[str, Any]], str] | None:
    """Get the custom output mapper for a graph ID, or None."""
    return _output_mappers.get(graph_id)
