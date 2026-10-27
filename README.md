# Graph benchmarks: LDBC SNB SF1

This repository compares graph systems using 30 custom queries over the LDBC Social Network Benchmark (SNB) SF1 dataset. The queries explore n-hop traversals with different cardinalities, filters and projections.

## Licensing, provenance and benchmark status

The project is maintained by [HDC Labs](https://github.com/hyperdimensionalcomputingai/graph-benchmark-ldbc) and adopts [Apache License 2.0](LICENSE) for this derivative and future contributions. Inherited MIT-covered code and documentation from pre-change commit [`d7d56b2`](https://github.com/hyperdimensionalcomputingai/graph-benchmark-ldbc/tree/d7d56b29b39fdc4304639aed6bad2d465ba95488) retain their original MIT grant and the complete [MIT licence and copyright notice](LICENSES/MIT.txt).

The software distribution is described by `Apache-2.0 AND MIT`: Apache terms apply to the derivative, and MIT notices must be preserved for inherited portions. This is not a choice of either licence for the whole distribution. Earlier MIT releases remain MIT; this change does not replace earlier contributors' grants or imply that they newly grant Apache's explicit patent rights. The organization transfer does not assign copyright. See [third-party provenance and review gaps](THIRD_PARTY_NOTICES.md) and [contribution guidance](CONTRIBUTING.md).

The SNB dataset and data model originate with the Linked Data Benchmark Council (LDBC), now the Graph Data Council (GDC). Dataset files are downloaded from the [official source](https://ldbcouncil.org/benchmarks/snb/datasets/), rather than distributed in this repository. Their original rights and distribution conditions remain applicable; the repository's code licences do not cover them. The Fair Use Policy is not an artefact-specific dataset licence. The two images under `assets/` also have unresolved provenance and are not represented as Apache- or MIT-licensed by this change; see the specific review questions in the notices.

The 30 queries form a custom workload, not the official LDBC SNB workload. This project has not been audited, approved or endorsed by GDC.

**These are not LDBC Benchmark Results.** See the [GDC Fair Use Policy](https://ldbcouncil.org/benchmarks/fair-use-policies/).

The following systems are compared:
- Neo4j
- Kuzu (now archived)
- Ladybug
- lance-graph
- DuckPGQ (DuckDB with the SQL/PGQ community extension)
- FalkorDB
- lance-csr (a fork of lance-graph with a CSR adjacency index; its own uv project in [`lance_csr/`](lance_csr/README.md))

## Setup

We use [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage the dependencies.

```sh
# Sync the dependencies locally
uv sync --locked
```
All the dependencies are listed in `pyproject.toml`.

## Dataset

Download the SNB Interactive v1 initial SF1 dataset (`CsvBasic`, `StringDateFormatter`) with `download_dataset.py`. Install `curl`, `tar` and either `zstd` or `unzstd` first. The script extracts the archive into `csv/` and skips downloading if that directory already exists. It prints a SHA-256 hash, but no upstream expected checksum is configured; this is not an integrity verification against a published digest.

```bash
uv run download_dataset.py
```

Alternatively, navigate to the [LDBC site](https://ldbcouncil.org/benchmarks/snb/datasets/) and manually download and unzip the dataset from [this URL](https://datasets.ldbcouncil.org/snb-interactive-v1/social_network-sf1-CsvBasic-StringDateFormatter.tar.zst).

The schema of the LDBC SNB graph is shown below. There are 8 node types and 23 relationship types in the graph.

![](assets/ldbc-snb-schema.png)

The individual and total number of nodes and relationships in the graph are shown below.

```
Node counts:
- Comment: 2052169
- Forum: 90492
- Organisation: 7955
- Person: 9892
- Place: 1460
- Post: 1003605
- Tag: 16080
- Tagclass: 71

Relationship counts:
- commentHasCreator: 2052169
- commentHasTag: 2698393
- commentIsLocatedIn: 2052169
- containerOf: 1003605
- forumHasTag: 309766
- hasInterest: 229166
- hasMember: 1611869
- hasModerator: 90492
- hasType: 16080
- isPartOf: 1454
- isSubclassOf: 70
- knows: 180623
- likeComment: 1438418
- likePost: 751677
- organisationIsLocatedIn: 7955
- personIsLocatedIn: 9892
- postHasCreator: 1003605
- postHasTag: 713258
- postIsLocatedIn: 1003605
- replyOfComment: 1040749
- replyOfPost: 1011420
- studyAt: 7949
- workAt: 21654

Totals:
- nodes: 3181724
- relationships: 17256038
```

In total, there are 3.1M nodes and 17M relationships for the SF1 variant of this dataset.

## Ingest the data as a graph

Navigate to the individual directories to see the instructions on how to ingest the data into each graph system.
Once constructed, the graph is well-connected and has rich relationships between nodes of different types.

![](assets/./ldbc-snb-sf1-graph.png)

## Queries

Navigate to each directory and see the `query.py` files for
each of the 30 queries run in the benchmark.

## High-level results

**These are not LDBC Benchmark Results.** These independent, unaudited measurements apply to the configurations below.

Neo4j, Kuzu, Ladybug and lance-graph were measured back to back on **2026-10-24** with `./run_benchmarks.sh`. lance-csr 0.3.1 was re-run on its own with `./run_benchmarks.sh lance_csr` on **2026-10-27**, on battery power, which can throttle the CPU ([`results/environment.yml`](results/environment.yml)). DuckPGQ and FalkorDB results are from the earlier run on **2026-10-16**. All runs used the same machine:

| | |
| --- | --- |
| Machine | Apple M5 MacBook Pro (`Mac17,2`), 10 CPU cores (4 performance + 6 efficiency), 24 GiB unified memory |
| OS | macOS 26.6.2 (25G83) |
| Python | 3.13.14, pytest 9.0.2, pytest-benchmark 5.2.3 |
| Embedded engines | Run natively in-process, with no container VM running |
| Neo4j | Docker Desktop (engine 29.8.1), native arm64 Linux VM with 10 CPUs and 19.3 GiB RAM, using the heap/page-cache settings in `neo4j/docker-compose.yml` |
| FalkorDB | Same Docker VM as Neo4j, using `falkordb/docker-compose.yml` (server-side timeouts off, unlimited result set). The idle Neo4j container was still running |

Engine versions:

- **Neo4j 2026.09.0** Community Edition (previously 2025.12.1)
- **Kuzu 0.11.3** (unchanged)
- **Ladybug 0.21.2** (previously 0.21.1). All 30 queries use plain `conn.execute(query)`; `ANALYZE`, result cleanup and the six ART secondary indexes remain enabled
- **lance-graph 0.5.4** (unchanged)
- **lance-csr 0.3.1** (previously 0.2.0), a fork of lance-graph with a CSR adjacency index, running lance-graph's 30 queries over the same Lance datasets in two modes: tables in memory, and Lance datasets read lazily from disk. See the [lance-csr README](lance_csr/README.md)
- **DuckPGQ** on DuckDB 1.5.6 (extension build `61f5d082`), new in this run, with the six ART indexes that mirror Ladybug's
- **FalkorDB 6.0.2**, new in this run, running Neo4j's 30 Cypher queries unmodified, with ID indexes plus seven secondary range indexes similar to Ladybug's ART indexes

Every graph was rebuilt from the CSVs before timing and verified to contain 3,181,724 nodes and 17,256,038 relationships. Every engine passed all 30 result assertions, with at least five measured rounds per query, except FalkorDB: its Q30 hit the 10-second query limit, and its other 29 queries passed. These runs compare the stated deployment configurations: Neo4j and FalkorDB run as servers inside a VM, while the others run embedded. The resource limits are not equal and caches are not controlled cold.

### Benchmark settings

Run from each engine directory:

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

`./run_benchmarks.sh` runs every engine with these settings, one after another, writes each engine's output to `results/` and records the date, machine and OS in `results/environment.yml`. Pass engine directories to run a subset, for example `./run_benchmarks.sh kuzu lance_csr`.

Five rounds is a minimum, not an exact count. Query result conversion and printing stay inside the timed functions. Calibration is enabled and warmup is disabled.

Every Neo4j, Kuzu, Ladybug, DuckPGQ and FalkorDB query has a 10-second timeout; set `QUERY_TIMEOUT_SECONDS` to change it. A query that takes longer is treated as broken: it fails with `TimeoutError` instead of being timed, so one bad plan cannot stretch a run of at least five rounds into hours, and `results/compare.py` shows it as `timeout` in the table. The slowest query in the table below takes about one second. Neo4j applies the limit as a transaction timeout, Kuzu and Ladybug use `Connection.set_query_timeout`, DuckPGQ cancels the query from a watchdog thread with DuckDB's `interrupt()`, and FalkorDB passes a per-query `timeout` to `GRAPH.RO_QUERY`. lance-graph 0.5.4 can neither time out nor cancel a query, and the lance-csr runner doesn't set lance-csr's `timeout`, so both run without a limit.

### Mean query latency

Times are in milliseconds. The ratio in parentheses is Neo4j mean / engine mean, so a value above 1 means the engine was faster than this Neo4j setup.

| Query | neo4j-2026.09.0 (ms) | kuzu-0.11.3 (ms) | ladybug-0.21.2 (ms) | lance-graph-0.5.4 (ms) | duckpgq-1.5.6 (ms) | falkordb-6.0.2 (ms) | lance-csr-0.3.1-lazy (ms) | lance-csr-0.3.1-memory (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| q1 | 1.277 | 1.734 (0.74x) | 1.218 (1.05x) | 1.297 (0.98x) | 0.978 (1.31x) | 0.440 (2.90x) | 1.185 (1.08x) | 0.687 (1.86x) |
| q2 | 3.260 | 1.322 (2.47x) | 1.123 (2.90x) | 2.337 (1.39x) | 3.450 (0.94x) | 4.682 (0.70x) | 1.418 (2.30x) | 0.503 (6.49x) |
| q3 | 0.665 | 1.034 (0.64x) | 0.789 (0.84x) | 1.862 (0.36x) | 1.120 (0.59x) | 4.420 (0.15x) | 0.802 (0.83x) | 0.686 (0.97x) |
| q4 | 2.656 | 0.848 (3.13x) | 0.393 (6.75x) | 2.982 (0.89x) | 1.545 (1.72x) | 0.215 (12.35x) | 0.779 (3.41x) | 0.501 (5.30x) |
| q5 | 2.785 | 3.440 (0.81x) | 4.004 (0.70x) | 2.044 (1.36x) | 2.014 (1.38x) | 1.211 (2.30x) | 2.377 (1.17x) | 0.864 (3.23x) |
| q6 | 2.597 | 0.664 (3.91x) | 0.787 (3.30x) | 0.727 (3.57x) | 0.554 (4.69x) | 0.193 (13.44x) | 0.825 (3.15x) | 0.443 (5.87x) |
| q7 | 0.430 | 27.735 (0.02x) | 25.112 (0.02x) | 15.677 (0.03x) | 2.666 (0.16x) | 0.649 (0.66x) | 1.055 (0.41x) | 0.999 (0.43x) |
| q8 | 7.287 | 2.723 (2.68x) | 3.375 (2.16x) | 1.141 (6.39x) | 1.825 (3.99x) | 1.801 (4.05x) | 1.738 (4.19x) | 0.624 (11.67x) |
| q9 | 0.758 | 1.728 (0.44x) | 1.342 (0.56x) | 1.888 (0.40x) | 1.158 (0.65x) | 0.235 (3.23x) | 1.416 (0.54x) | 0.791 (0.96x) |
| q10 | 3.788 | 1.553 (2.44x) | 1.778 (2.13x) | 26.693 (0.14x) | 2.728 (1.39x) | 0.201 (18.84x) | 0.955 (3.97x) | 0.700 (5.41x) |
| q11 | 10.282 | 7.960 (1.29x) | 4.635 (2.22x) | 3.084 (3.33x) | 2.690 (3.82x) | 6.742 (1.53x) | 2.072 (4.96x) | 1.467 (7.01x) |
| q12 | 2.549 | 17.156 (0.15x) | 7.840 (0.33x) | 18.684 (0.14x) | 4.340 (0.59x) | 1.125 (2.27x) | 7.077 (0.36x) | 0.676 (3.77x) |
| q13 | 6.654 | 42.661 (0.16x) | 5.837 (1.14x) | 9.616 (0.69x) | 3.382 (1.97x) | 2.522 (2.64x) | 1.011 (6.58x) | 0.731 (9.11x) |
| q14 | 0.460 | 1.556 (0.30x) | 0.902 (0.51x) | 2.909 (0.16x) | 1.439 (0.32x) | 0.204 (2.26x) | 0.637 (0.72x) | 0.477 (0.96x) |
| q15 | 2.369 | 2.379 (1.00x) | 1.164 (2.04x) | 3.023 (0.78x) | 1.295 (1.83x) | 0.226 (10.49x) | 0.745 (3.18x) | 0.512 (4.63x) |
| q16 | 1.260 | 1.775 (0.71x) | 1.036 (1.22x) | 4.329 (0.29x) | 3.400 (0.37x) | 4.415 (0.29x) | 1.079 (1.17x) | 0.641 (1.97x) |
| q17 | 3.086 | 2.616 (1.18x) | 1.738 (1.78x) | 2.301 (1.34x) | 1.365 (2.26x) | 1.199 (2.57x) | 1.413 (2.18x) | 0.934 (3.30x) |
| q18 | 3.108 | 1.508 (2.06x) | 1.221 (2.55x) | 1.763 (1.76x) | 1.047 (2.97x) | 0.628 (4.95x) | 1.102 (2.82x) | 0.652 (4.77x) |
| q19 | 4.856 | 11.657 (0.42x) | 3.433 (1.41x) | 19.927 (0.24x) | 4.327 (1.12x) | 2.129 (2.28x) | 1.364 (3.56x) | 0.975 (4.98x) |
| q20 | 421.921 | 13.247 (31.85x) | 14.154 (29.81x) | 3.132 (134.71x) | 0.956 (441.15x) | 0.455 (926.79x) | 17.087 (24.69x) | 2.152 (196.02x) |
| q21 | 0.511 | 0.441 (1.16x) | 0.500 (1.02x) | 1.459 (0.35x) | 0.662 (0.77x) | 0.346 (1.48x) | 0.801 (0.64x) | 0.707 (0.72x) |
| q22 | 2.657 | 23.338 (0.11x) | 7.456 (0.36x) | 13.413 (0.20x) | 5.143 (0.52x) | 0.670 (3.97x) | 0.987 (2.69x) | 0.648 (4.10x) |
| q23 | 3.133 | 1.187 (2.64x) | 0.791 (3.96x) | 2.419 (1.30x) | 1.131 (2.77x) | 0.299 (10.49x) | 1.189 (2.64x) | 0.664 (4.72x) |
| q24 | 0.717 | 1.233 (0.58x) | 0.812 (0.88x) | 1.754 (0.41x) | 0.705 (1.02x) | 0.201 (3.56x) | 1.017 (0.70x) | 0.623 (1.15x) |
| q25 | 2.858 | 1.453 (1.97x) | 1.269 (2.25x) | 1.468 (1.95x) | 0.850 (3.36x) | 0.175 (16.30x) | 1.220 (2.34x) | 0.724 (3.95x) |
| q26 | 0.649 | 3.372 (0.19x) | 1.147 (0.57x) | 2.932 (0.22x) | 1.489 (0.44x) | 0.299 (2.17x) | 1.063 (0.61x) | 0.697 (0.93x) |
| q27 | 2.219 | 17.960 (0.12x) | 3.708 (0.60x) | 24.840 (0.09x) | 2.881 (0.77x) | 0.767 (2.89x) | 1.394 (1.59x) | 0.800 (2.77x) |
| q28 | 2.369 | 1.513 (1.57x) | 1.776 (1.33x) | 2.498 (0.95x) | 1.171 (2.02x) | 4.895 (0.48x) | 2.271 (1.04x) | 1.300 (1.82x) |
| q29 | 2.621 | 1.022 (2.56x) | 0.718 (3.65x) | 2.963 (0.88x) | 1.231 (2.13x) | 4.379 (0.60x) | 0.976 (2.69x) | 0.666 (3.94x) |
| q30 | 1,359.978 | 146.520 (9.28x) | 97.766 (13.91x) | 34.313 (39.63x) | 26.809 (50.73x) | timeout | 50.468 (26.95x) | 49.638 (27.40x) |

![](results/benchmark_heatmap.png)

FalkorDB's Q30 shows as `timeout` because it exceeds the 10-second limit. Without the limit it averaged 61.9 s over five rounds on the same M5 ([CLI output](results/archived/falkordb-6.0.2-q30-no-limit.txt)): the current planner pairs every person's comments with all of their posts (about 447M candidate pairs) before checking `replyOfPost`. See the [FalkorDB README](falkordb/README.md#results).
