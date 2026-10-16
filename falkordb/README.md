# FalkorDB

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

Measured on **2026-10-10** on an AMD Ryzen 9 6900HS (16 logical CPUs, 30 GiB RAM) running Linux 7.1.3 and Python 3.14.8, with FalkorDB 6.0.2 in Docker started from the provided `docker-compose.yml` (`THREAD_COUNT` and `OMP_THREAD_COUNT` 16, query timeouts disabled, unlimited result set size). This is a different machine from the Apple M5 used for the other engines, so these numbers are not directly comparable with the main table.

[CLI output](../results/falkordb-6.0.2.txt) · [Raw benchmark JSON](../results/falkordb-6.0.2.json)

After loading, `GRAPH.MEMORY USAGE` reports 2.97 GB for the graph. Ingestion took about 20 minutes, almost all of it for the 17,256,038 relationships; it was timed on a busy machine, so treat that as approximate.

All 30 queries passed their result assertions with the benchmark settings above. Apart from Q30, every query averages under 10 ms. Q30 averages 75.2 s over five rounds: the planner starts from each `Person`, pairs all of that person's comments with all of their posts (about 447M candidate pairs) and only then checks `replyOfPost`. The query text is identical to Neo4j's for all 30 queries.
