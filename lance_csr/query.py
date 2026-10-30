"""Run lance_graph/query.py's 30 queries on lance-csr.

The queries and data (lance_graph/graph_lance) are shared with lance-graph, so both engines answer
identical Cypher over identical Lance datasets. The graph mapping is the same, but built with
lance-csr's node_table and rel_table, which also name each relationship's endpoint node tables.

LANCE_CSR_MODE picks how the datasets are read; both use CSR traversal (use_csr=True):
- memory (default): every table loaded into memory as Arrow, as lance-graph's benchmark does
- lazy: Lance datasets read from disk as queries need them
"""

import functools
import importlib.util
import os
import sys
from pathlib import Path

import lance
import lance_csr

MODE = os.environ.get("LANCE_CSR_MODE", "memory")
if MODE not in ("memory", "lazy"):
    raise ValueError(f"LANCE_CSR_MODE must be 'memory' or 'lazy', not {MODE!r}")

# lance_graph/query.py imports `lance_graph`; point that at lance-csr.
sys.modules["lance_graph"] = lance_csr
_path = Path(__file__).resolve().parent.parent / "lance_graph" / "query.py"
_spec = importlib.util.spec_from_file_location("lance_graph_query", _path)
q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q)

q.CypherEngine = functools.partial(lance_csr.CypherEngine, use_csr=True)


def build_config() -> lance_csr.GraphConfig:
    # lance-csr's rel_table names the node tables at both ends; read them from the dataset names,
    # such as person_likes_post for Person to Post.
    labels = {label.lower(): label for label in q.NODE_LABELS}
    builder = lance_csr.GraphConfig.builder()
    for label in q.NODE_LABELS:
        builder = builder.node_table(label, "id")
    for rel_type, dataset_name in q.REL_DATASETS.items():
        parts = dataset_name.split("_")
        builder = builder.rel_table(rel_type, labels[parts[0]], labels[parts[-1]], "src", "dst")
    return builder.build()


q.build_config = build_config
if MODE == "lazy":
    def load_datasets(root: Path) -> dict[str, lance.LanceDataset]:
        names = {label: label for label in q.NODE_LABELS} | q.REL_DATASETS
        return {key: lance.dataset(str(root / f"{name}.lance")) for key, name in names.items()}

    q.load_datasets = load_datasets

if __name__ == "__main__":
    q.main(q._parse_selection(sys.argv[1:]))
