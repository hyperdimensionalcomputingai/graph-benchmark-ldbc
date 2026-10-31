# lance-csr

This section describes how to run the 30 queries on [lance-csr](https://github.com/hyperdimensionalcomputingai/lance-csr), an embedded Cypher engine over [Lance](https://lancedb.github.io/lance/) datasets with a CSR adjacency index. It is a fork of lance-graph.

This directory has no queries or data of its own. `query.py` loads [`../lance_graph/query.py`](../lance_graph/query.py) with `lance_graph` pointed at `lance_csr`, and `benchmark_query.py` reuses [`../lance_graph/benchmark_query.py`](../lance_graph/benchmark_query.py). Both engines therefore run the same 30 Cypher queries and assertions over the same `../lance_graph/graph_lance` datasets.

## Setup

lance-csr is embedded: it runs inside the Python process, with no server. This directory is its own uv project, because lance-csr 0.5.1 needs pylance 13 while the root project's lance-graph 0.5.4 uses pylance 1.0.4. Build the Lance datasets first (see [lance-graph](../lance_graph/README.md)), then install:

```sh
uv sync --frozen
```

## Modes

`LANCE_CSR_MODE` selects how the engine reads the datasets. Both modes use CSR traversal (`use_csr=True`).

| Mode | Inputs |
| --- | --- |
| `memory` (default) | every table loaded into memory as Arrow, as lance-graph's benchmark does |
| `lazy` | Lance datasets read from disk as queries need them |

## Execute queries

```sh
uv run query.py "1,2,6"
```

### Run benchmark

From the repository root, `./run_benchmarks.sh lance_csr` runs both modes with the settings in the [root README](../README.md#benchmark-settings) and writes the output to `results/`. To run one mode:

```sh
LANCE_CSR_MODE=memory uv run --frozen pytest benchmark_query.py --benchmark-min-rounds=5 --benchmark-disable-gc
```

The runner doesn't pass lance-csr's `timeout` argument, so `QUERY_TIMEOUT_SECONDS` doesn't apply and queries run without a limit. `query.py` replaces the shared module's `build_config()`, which uses lance-graph's builder methods, with one that uses lance-csr's `node_table` and `rel_table`. It reads each relationship's endpoint node tables from its dataset name (`person_likes_post` goes from `Person` to `Post`).
