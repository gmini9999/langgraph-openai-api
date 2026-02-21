"""Test dynamic graph loading."""

import pytest

from langgraph_openai_api.graph.loader import load_graph


def test_load_graph_from_file(test_graph_file):
    config_path, graph_path = test_graph_file
    base_dir = str(config_path.parent)
    graph = load_graph("./graph.py:graph", base_dir=base_dir)
    assert graph is not None
    assert hasattr(graph, "ainvoke")


def test_load_graph_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_graph("./nonexistent.py:graph", base_dir=str(tmp_path))


def test_load_graph_variable_not_found(tmp_path):
    code = "x = 42\n"
    (tmp_path / "test.py").write_text(code)
    with pytest.raises(AttributeError, match="not_a_graph"):
        load_graph("./test.py:not_a_graph", base_dir=str(tmp_path))
