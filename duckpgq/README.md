# DuckPGQ

This section describes how to benchmark the LDBC SNB SF1 data in [DuckDB](https://duckdb.org/) using the [DuckPGQ](https://duckpgq.org/) community extension. DuckPGQ adds SQL/PGQ (the graph query extension of the SQL:2023 standard) to DuckDB: the graph is declared as a *property graph* over regular DuckDB tables and queried with `GRAPH_TABLE (... MATCH ...)` clauses embedded in SQL.

The scripts target DuckDB 1.5.6 (the `duckdb` wheel from PyPI, pinned in `pyproject.toml`) with the DuckPGQ community extension published for that release.

## Setup

DuckDB is an embedded database, so there is no server to run. The `duckdb` Python package is part of the project dependencies; run `uv sync --frozen` from the repository root. The DuckPGQ community extension is installed from the DuckDB community extension repository the first time the scripts run:

```sql
INSTALL duckpgq FROM community;
LOAD duckpgq;
```

All scripts in this directory go through `common.py`, which opens the database (default `duckpgq/ldbc_snb_sf1.duckdb`, override with `DUCKPGQ_DB_PATH`) and loads the extension.

## Build graph

`build_graph.py` reads the pipe-delimited LDBC CSV files under `../csv` (see `download_dataset.py` in the repository root) into DuckDB tables with the same schema as the other engines, creates the secondary indexes, and declares the property graph.

```sh
uv run build_graph.py
```

Every node table has `id BIGINT PRIMARY KEY`; edge tables have `src`/`dst` columns plus any edge properties (`joinDate`, `creationDate`, `classYear`, `workFrom`). The property graph maps each table to a label of the same name. Print the full DDL with `uv run build_graph.py --print-ddl`; it has this shape:

```sql
CREATE PROPERTY GRAPH snb
    VERTEX TABLES (
        Comment LABEL Comment,
        Forum LABEL Forum,
        ...
    )
    EDGE TABLES (
        containerOf
            SOURCE KEY (src) REFERENCES Forum (id)
            DESTINATION KEY (dst) REFERENCES Post (id)
            LABEL containerOf,
        commentHasCreator
            SOURCE KEY (src) REFERENCES Comment (id)
            DESTINATION KEY (dst) REFERENCES Person (id)
            LABEL commentHasCreator,
        ...
    );
```

Secondary (ART) indexes are created on the same `(table, column)` pairs as the Ladybug ART indexes: `Place.name`, `Tag.name`, `Person.firstName`, `Person.lastName`, `Person.birthday` and `Comment.length`. DuckDB only uses them for selective equality lookups; range and `contains` filters go through the zone-map pruned table scans.

A quick ablation (median of 15 runs per query, with and without the six indexes, same process, Apple M5 Pro) showed the indexes are neutral to mildly helpful: they speed up Q20 to Q25 by 1.2 to 1.6× and slow down Q28 and Q29 by about 1.3 to 1.6×, with the rest within noise. They are kept for parity with the Ladybug setup.

The whole build takes a few seconds (DuckDB reads the CSV files in parallel). Check the node and relationship counts against the root README with:

```sh
uv run count_nodes_and_rels.py
```

## Execute queries

`query.py` contains the 30 queries of the suite, translated from the Cypher versions in `ladybugdb/query.py` to SQL/PGQ. Run the full suite, or a comma-separated subset:

```sh
uv run query.py
uv run query.py "1,2,6"
```

Notes on the translation:

- The pattern inside `GRAPH_TABLE` returns a table via the `COLUMNS (...)` clause. `DISTINCT`, aggregations, `ORDER BY` and `LIMIT` are expressed in the surrounding SQL.
- DuckPGQ requires every node and edge pattern to bind a variable *and* a label, so `(:Tag)` and `-[:knows]->` become `(t:Tag)` and `-[k:knows]->`, and a variable reused across patterns repeats its label (`(p:Person)` in each pattern).
- Cypher `{ID: ...}` property shorthands become `WHERE` predicates, `CONTAINS` becomes `contains()`, and `DATE("...")` becomes `DATE '...'`.
- All patterns are written left to right along the edge direction (`(post:Post)-[hc:postHasCreator]->(p:Person)` rather than `(p)<-[:postHasCreator]-(post)`); DuckPGQ accepts both.
- Query parameters are literals, as in the Cypher versions.

DuckPGQ returns the same results as Ladybug on all 30 queries; `benchmark_query.py` asserts the same expected values as `ladybugdb/benchmark_query.py` (with the SQL column aliases).

### Run benchmark

Run from `duckpgq/`:

```sh
uv run --frozen pytest benchmark_query.py \
  --benchmark-min-rounds=5 \
  --benchmark-min-time=0.000005 \
  --benchmark-max-time=1.0 \
  --benchmark-timer=time.perf_counter \
  --benchmark-calibration-precision=10 \
  --benchmark-warmup=off \
  --benchmark-warmup-iterations=5 \
  --benchmark-disable-gc \
  --benchmark-sort=fullname
```

The results are output to a table that can be programmatically parsed for timing comparisons with other systems, in the same format as the other engines.
