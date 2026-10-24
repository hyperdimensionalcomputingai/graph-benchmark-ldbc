# Third-party provenance and notices

Reviewed on 2026-10-24 against pre-change remote `main` commit `d7d56b29b39fdc4304639aed6bad2d465ba95488`, the tracked tree and fetched Git history. This inventory covers this repository only.

## Licence and authorship

The root [LICENSE](LICENSE) contains Apache License 2.0 for the derivative and future contributions. The complete prior MIT text, including `Copyright (c) 2026 Prashanth Rao`, is preserved byte-for-byte in [LICENSES/MIT.txt](LICENSES/MIT.txt).

The inherited MIT-covered material is the repository software and associated documentation present at [pre-change commit `d7d56b29b39fdc4304639aed6bad2d465ba95488`](https://github.com/hyperdimensionalcomputingai/graph-benchmark-ldbc/tree/d7d56b29b39fdc4304639aed6bad2d465ba95488): the root downloader, six engine directories (queries, harnesses, ingestion helpers, Cypher and configuration), result-processing scripts and associated project documentation/configuration. Existing result artefacts remain unchanged; this code-licence statement does not establish rights in underlying data or third-party images. The dataset, data model, images and separately licensed dependencies below are not brought under Apache or MIT merely by inclusion or reference.

The [MIT licence](https://opensource.org/license/mit) permits sublicensing, subject to retaining its copyright and permission notice in copies or substantial portions. We use that permission to distribute an Apache-licensed derivative containing MIT-covered portions, not to replace every earlier contributor's original licence grant. Retain both licence texts and applicable notices when redistributing this combined software (`Apache-2.0 AND MIT` in package metadata, not `OR`). Previously distributed MIT versions remain available under MIT. No earlier MIT contributor is represented as newly granting the explicit patent licence in [Apache section 3](https://www.apache.org/licenses/LICENSE-2.0); Apache grants extend only to rights the relevant grantor can grant.

Git history records contributions by Prashanth Rao (prrao87), JoshuaTang, Arun Sharma, Darek and dtenwolde. Git authorship does not prove copyright ownership. The transfer to HDC Labs does not assign copyright, and no new organizational copyright claim is added. [Contribution guidance](CONTRIBUTING.md) applies prospectively.

The [ASF third-party policy](https://www.apache.org/legal/resolved.html#category-a) lists MIT as compatible for inclusion in Apache projects; it is supporting guidance, not a claim that this project belongs to the ASF. Apache section 4 requires applicable notices to be retained. No separate upstream NOTICE requirement was identified in the tracked code or licence history, so no speculative `NOTICE` is added.

| Material | Origin and revision evidence | Licence / terms | Use and adaptations |
| --- | --- | --- | --- |
| Custom queries and Python harness | Kuzu introduced in `640d94b`, Neo4j in `51a308b`, Ladybug in `1557825`, lance-graph in `c293bc5`, DuckPGQ in `a0cd1a6`, FalkorDB in `31026e6` | Retained [MIT licence](LICENSES/MIT.txt) for inherited portions; Apache-2.0 for the derivative and future contributions | Six query modules each define `run_query1` through `run_query30`; dialect and execution adaptations are recorded in Git. These are custom queries, not the official Interactive v1 suite. History does not independently prove that every contribution is original; maintainer confirmation remains pending. |
| LDBC/GDC SNB dataset and data model | [Official datasets](https://ldbcouncil.org/benchmarks/snb/datasets/); SNB Interactive v1 initial SF1, `CsvBasic`, `StringDateFormatter`; [exact archive](https://datasets.ldbcouncil.org/snb-interactive-v1/social_network-sf1-CsvBasic-StringDateFormatter.tar.zst) | Artefact-specific licence / redistribution terms unresolved; the Fair Use Policy is not a dataset licence | Downloaded by `download_dataset.py`, extracted to ignored `csv/`, then transformed by each engine's ingestion script. No dataset files found in the tracked tree or locally reachable history. No expected upstream checksum is configured. Do not redistribute the archive or extracted data until terms are confirmed. |
| `assets/ldbc-snb-schema.png` and `assets/ldbc-snb-sf1-graph.png` | Added by prrao87 in `1addafa`; schema depicts the LDBC SNB data model | Image source, creator, modifications and applicable terms unresolved | Both images are already distributed. Git identifies who added them, not who created them. Confirm attribution and redistribution rights, or replace/remove these specific assets before publication of the migration. |
| Python dependencies | Root `uv.lock` records PyPI sources, versions and distribution hashes | Each dependency retains its own licence | Installed dependencies, not vendored source. The root code licence does not relicense them. The DuckPGQ extension and container images also retain their own terms; they are fetched separately, not vendored here. |

LDBC/GDC is credited for the SNB dataset and data model. HDC Labs claims no ownership of third-party works. Applicable original licences and notices remain in force. No copied official LDBC query suite was identified in this checkout, so no upstream Apache NOTICE has been added speculatively.

**These are not LDBC Benchmark Results.** This custom workload is unaudited and is not approved or endorsed by GDC. See the [GDC Fair Use Policy](https://ldbcouncil.org/benchmarks/fair-use-policies/).

## Remaining review questions and migration status

- For `assets/ldbc-snb-schema.png` and `assets/ldbc-snb-sf1-graph.png`, obtain the original source, creator and licence or written redistribution permission (including required attribution), or replace/remove those specific assets before a release claiming cleared image rights. This licensing PR leaves them unchanged and does not resolve their rights. Confirm the exact dataset/data-model terms before redistribution. Maintainer confirmation of custom-code provenance remains pending; no specific incompatible code component was identified, so a general request for retroactive Apache consent is not a prerequisite for retaining MIT-covered code in this derivative.
- `neo4j/.env` was tracked in Git. It is now removed from tracking while the local file is retained and ignored. Its past contents remain in history: rotate any exposed password that was used elsewhere. History rewriting requires a separate decision.
- The earlier migration inventory covered locally reachable refs, not a fresh fetch or a dedicated secret scanner; its findings below are retained as historical context. This licensing review fetched origin but did not repeat the blob-size or secret scan. No dataset/archive paths were found; the largest historical blob was a curated result JSON of 1,241,081 bytes. Existing result logs include machine paths and metadata; they are retained as measurement evidence, not claimed to be anonymized.
- Preserve the curated results. No workload, query semantics or reported timings were changed. The README describes hardware, engine versions, timing boundaries and resource differences; these are historical measurements, not newly verified performance claims.
- The GitHub location and SSH origin are verified as `hyperdimensionalcomputingai/graph-benchmark-ldbc`; fetched remote `main` was `d7d56b29b39fdc4304639aed6bad2d465ba95488`. This PR does not change repository settings or audit collaborator permissions or old-URL redirects.

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

Licensing-change checks on 2026-10-24:

| Check | Outcome |
| --- | --- |
| Apache text against the ASF canonical text download | Byte-for-byte match, including sections 1–9 and appendix |
| Retained MIT against the pre-change commit | Byte-for-byte match, including copyright and disclaimer |
| Package metadata and licence-file paths | Consistent with `Apache-2.0 AND MIT`; all paths exist |
| Local Markdown links and anchors across READMEs and licensing guidance | 37 checked successfully |
| `uv lock --check --offline` and diff whitespace | Passed; lock unchanged |
| Executable code, queries, images and published results | Unchanged; benchmark reruns unnecessary |
