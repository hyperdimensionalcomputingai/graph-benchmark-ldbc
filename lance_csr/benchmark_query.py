"""lance_graph/benchmark_query.py (same tests and assertions) against lance-csr; see query.py for modes."""

import importlib.util
import sys
from pathlib import Path

import query

sys.modules["query"] = query.q
_path = Path(__file__).resolve().parent.parent / "lance_graph" / "benchmark_query.py"
_spec = importlib.util.spec_from_file_location("lance_graph_benchmark_query", _path)
_bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bench)

globals().update(
    {name: obj for name, obj in vars(_bench).items() if name.startswith("test_") or name == "graph_context"}
)
