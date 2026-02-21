"""Test graph registry."""

from langgraph_openai_api.graph.registry import GraphRegistry


def test_register_and_get():
    registry = GraphRegistry()
    registry.register("test-graph", "fake_graph_obj", created_at=1000)

    assert registry.exists("test-graph")
    assert registry.get("test-graph") == "fake_graph_obj"


def test_get_nonexistent():
    registry = GraphRegistry()
    assert registry.get("nope") is None
    assert not registry.exists("nope")


def test_list_graphs():
    registry = GraphRegistry()
    registry.register("a", "ga", created_at=100)
    registry.register("b", "gb", created_at=200)

    graphs = registry.list_graphs()
    assert len(graphs) == 2
    ids = [g["id"] for g in graphs]
    assert "a" in ids
    assert "b" in ids


def test_graph_ids():
    registry = GraphRegistry()
    registry.register("x", "gx")
    registry.register("y", "gy")
    assert set(registry.graph_ids()) == {"x", "y"}
