"""Dynamic graph loader from module paths."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def load_graph(module_path: str, base_dir: str = ".") -> Any:
    """Load a compiled graph from a module path.

    Args:
        module_path: Format "path/to/module.py:variable_name"
        base_dir: Base directory for resolving relative paths.

    Returns:
        The graph object from the module.

    Raises:
        FileNotFoundError: If the module file doesn't exist.
        AttributeError: If the variable doesn't exist in the module.
    """
    file_path, var_name = module_path.rsplit(":", 1)
    resolved = (Path(base_dir) / file_path).resolve()

    if not resolved.exists():
        raise FileNotFoundError(f"Graph module not found: {resolved}")

    module_name = f"langgraph_openai_api._loaded_.{resolved.stem}_{id(resolved)}"

    spec = importlib.util.spec_from_file_location(module_name, str(resolved))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {resolved}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    graph = getattr(module, var_name, None)
    if graph is None:
        raise AttributeError(f"Variable '{var_name}' not found in {resolved}")

    return graph
