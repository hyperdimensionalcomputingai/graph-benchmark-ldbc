# Third-party provenance and notices

Reviewed on 2026-10-24 against repository commit `73fa7106527552b8daaad93836aafe22d9ee0532` and locally available Git history. This inventory covers this repository only.

## Licence and authorship

The root [LICENSE](LICENSE) remains MIT, including `Copyright (c) 2026 Prashanth Rao`. No relicensing or copyright reassignment is part of the migration preparation. Git history also records contributions by JoshuaTang, Arun Sharma, Darek and dtenwolde. Git authorship is evidence of contributions, not proof of copyright ownership or consent to relicense.

| Material | Origin and revision evidence | Licence / terms | Use and adaptations |
| --- | --- | --- | --- |
| Custom queries and Python harness | Kuzu introduced in `640d94b`, Neo4j in `51a308b`, Ladybug in `1557825`, lance-graph in `c293bc5`, DuckPGQ in `a0cd1a6`, FalkorDB in `31026e6` | Existing repository MIT licence; preserve contributor rights | Six query modules each define `run_query1` through `run_query30`; dialect and execution adaptations are recorded in Git. These are custom queries, not the official Interactive v1 suite. History does not independently prove that every contribution is original; maintainer confirmation remains pending. |
| LDBC/GDC SNB dataset and data model | [Official datasets](https://ldbcouncil.org/benchmarks/snb/datasets/); SNB Interactive v1 initial SF1, `CsvBasic`, `StringDateFormatter`; [exact archive](https://datasets.ldbcouncil.org/snb-interactive-v1/social_network-sf1-CsvBasic-StringDateFormatter.tar.zst) | Artefact-specific licence / redistribution terms unresolved; the Fair Use Policy is not a dataset licence | Downloaded by `download_dataset.py`, extracted to ignored `csv/`, then transformed by each engine's ingestion script. No dataset files found in the tracked tree or locally reachable history. No expected upstream checksum is configured. Do not redistribute the archive or extracted data until terms are confirmed. |
| `assets/ldbc-snb-schema.png` and `assets/ldbc-snb-sf1-graph.png` | Added by prrao87 in `1addafa`; schema depicts the LDBC SNB data model | Image source, creator, modifications and applicable terms unresolved | Both images are already distributed. Git identifies who added them, not who created them. Confirm attribution and redistribution rights, or replace/remove these specific assets before publication of the migration. |
| Python dependencies | Root `uv.lock` records PyPI sources, versions and distribution hashes | Each dependency retains its own licence | Installed dependencies, not vendored source. The root MIT licence does not relicense them. |

LDBC/GDC is credited for the SNB dataset and data model. HDC Labs claims no ownership of third-party works. Applicable original licences and notices remain in force. No copied official LDBC query suite was identified in this checkout, so no upstream Apache NOTICE has been added speculatively.

**These are not LDBC Benchmark Results.** This custom workload is unaudited and is not approved or endorsed by GDC. See the [GDC Fair Use Policy](https://ldbcouncil.org/benchmarks/fair-use-policies/).

## Before transfer

- Confirm the outstanding image rights and contributor provenance above. Retain MIT unless a separately approved rights review supports relicensing.
- `neo4j/.env` was tracked in Git. It is now removed from tracking while the local file is retained and ignored. Its past contents remain in history: rotate any exposed password that was used elsewhere. History rewriting requires a separate decision.
- The history inventory covered locally reachable refs, not a fresh fetch or a dedicated secret scanner. No dataset/archive paths were found; the largest historical blob was a curated result JSON of 1,241,081 bytes. Existing result logs include machine paths and metadata; they are retained as measurement evidence, not claimed to be anonymized.
- Preserve the curated results. No workload, query semantics or reported timings were changed. The README describes hardware, engine versions, timing boundaries and resource differences; these are historical measurements, not newly verified performance claims.
- GitHub transfer, remote URL changes, permissions and redirect checks are still pending. No transfer or repository settings changes were made.

## Local validation

Root dependency setup: `uv sync --locked` (the preparation check used `--offline` with the installed environment). This does not establish a clean-machine install.

Collect each engine separately because the harnesses import their local `query` module:

```sh
(cd neo4j && uv run --frozen pytest benchmark_query.py --collect-only -q)
```

Repeat for `kuzu`, `ladybugdb`, `lance_graph`, `duckpgq` and `falkordb`. After downloading and ingesting data using each engine's README, use `uv run --frozen query.py "1,2,6"` from that engine directory for a small execution check, then the benchmark command in the root README for a full run. Execution checks require populated databases and, for server engines, running services; collection alone does not validate results.

Preparation checks completed on 2026-10-24:

| Check | Outcome |
| --- | --- |
| Root locked dependency sync, offline | Passed against installed environment |
| Test collection, six root-project engines | 30 tests per engine; 180 total collected successfully |
| Tracked Python syntax, documentation local links, diff whitespace | Passed |
| Local `.env` retained, untracked and ignored; example remains trackable | Passed |
| Dataset download, database ingestion, query execution and performance reruns | Skipped; this patch changes documentation, metadata and tracking only |
