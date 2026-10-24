# FalkorDB

**These are not LDBC Benchmark Results.** See the repository’s [benchmark status and provenance](../README.md#licensing-provenance-and-benchmark-status).

This section describes how to benchmark the social network data in [FalkorDB](https://github.com/FalkorDB/FalkorDB), a graph database built as a Redis module. Version 6.0 replaced the 4.x C engine with a new engine written in Rust; the commands and Cypher are unchanged.

## Setup

FalkorDB runs as a server. Start it via Docker using the provided `docker-compose.yml`, which pins the image to `6.0.2`:

```sh
docker compose up -d
```

The scripts connect with the [`falkordb`](https://pypi.org/project/falkordb/) Python client and are configured via environment variables:

- `FALKORDB_HOST` (optional, defaults to `localhost`)
- `FALKORDB_PORT` (optional, defaults to `6379`; also sets the host port in `docker-compose.yml`)
- `FALKORDB_GRAPH` (optional, defaults to `ldbc_snb_sf1`)
- `FALKORDB_VERSION` (optional, Docker image tag, defaults to `6.0.2`)
- `QUERY_TIMEOUT_SECONDS` (optional, defaults to `10`)

## Build graph

The script `build_graph.py` drops any existing graph with the same name, creates a range index on `ID` for each node label, then ingests the CSV files in batches with `UNWIND ... CREATE`. Edges look up both endpoints through the `ID` indexes. After ingestion it builds range indexes on the selectively filtered properties (`Place.name`, `Tag.name`, `Tagclass.name`, `Organisation.name`, `Person.firstName`, `Person.lastName`, `Comment.length`), waits until every index is operational, and prints the total node and relationship counts.

The secondary indexes follow Ladybug's ART indexes with two differences. There is no index on `Person.birthday`, because Q8 filters on `date(p.birthday)` and a property index cannot serve that predicate. `Organisation.name` and `Tagclass.name` are indexed for their equality filters; Ladybug leaves them out because they slowed down its engine on these small tables. Neo4j, Kuzu and lance-graph use ID indexes only.

```sh
uv run build_graph.py
```

## Visualize graph

The FalkorDB image ships with the FalkorDB Browser, available at `http://localhost:3000`.

## Execute queries

The query suite consists of the same 30 Cypher queries used for Neo4j, unchanged. Each query is sent with `GRAPH.RO_QUERY`.

Run the full query suite using the provided script below.

```bash
uv run query.py
```

Run a subset by passing a comma-separated list of query numbers:

```bash
uv run query.py "1,2,6"
```

### Run benchmark

Run from `falkordb/`:

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

## Results

Measured on **2026-10-16** on the Apple M5 used for the other engines (see the [main README](../README.md#high-level-results)), with FalkorDB 6.0.2 in Docker Desktop started from the provided `docker-compose.yml` (`THREAD_COUNT` and `OMP_THREAD_COUNT` 10, server-side query timeouts disabled, unlimited result set size) and the harness's 10-second per-query timeout. FalkorDB is the last column of the main table.

[CLI output](../results/falkordb-6.0.2.txt) · [Raw benchmark JSON](../results/falkordb-6.0.2.json)

After loading, `GRAPH.MEMORY USAGE` reports 2,824 MB for the graph. `build_graph.py` took about 11.5 minutes, almost all of it for the 17,256,038 relationships.

Q30 exceeds the 10-second limit and fails with `TimeoutError`. Run on its own with `QUERY_TIMEOUT_SECONDS=600`, it averaged 61.9 s over five rounds on the M5 ([CLI output](../results/archived/falkordb-6.0.2-q30-no-limit.txt)), and 75.2 s on the Ryzen 9 6900HS. Its planner starts from each `Person`, pairs all of that person's comments with all of their posts (about 447M candidate pairs) and only then checks `replyOfPost`. The other 29 queries pass their result assertions and average under 7 ms (slowest: Q11 at 6.7 ms). The query text is identical to Neo4j's for all 30 queries.

The earlier run on the Ryzen 9 6900HS (16 logical CPUs, 30 GiB RAM, Linux 7.1.3, Python 3.14.0, 2026-10-10) is archived: [CLI output](../results/archived/falkordb-6.0.2-ryzen-2026-10-10.txt) · [Raw benchmark JSON](../results/archived/falkordb-6.0.2-ryzen-2026-10-10.json)
