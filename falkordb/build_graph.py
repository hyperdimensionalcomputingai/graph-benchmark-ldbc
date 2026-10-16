import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl
from dotenv import load_dotenv
from falkordb import FalkorDB, Graph

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_ROOT = REPO_ROOT / "csv"
DYNAMIC_ROOT = CSV_ROOT / "dynamic"
STATIC_ROOT = CSV_ROOT / "static"

FALKORDB_HOST = os.environ.get("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.environ.get("FALKORDB_PORT", "6379"))
FALKORDB_GRAPH = os.environ.get("FALKORDB_GRAPH", "ldbc_snb_sf1")

JsonBlob = dict[str, Any]


@dataclass(frozen=True)
class EdgeSpec:
    path: Path
    src_label: str
    rel_type: str
    dst_label: str


NODE_FILES: dict[str, Path] = {
    "Comment": DYNAMIC_ROOT / "comment_0_0.csv",
    "Forum": DYNAMIC_ROOT / "forum_0_0.csv",
    "Person": DYNAMIC_ROOT / "person_0_0.csv",
    "Post": DYNAMIC_ROOT / "post_0_0.csv",
    "Organisation": STATIC_ROOT / "organisation_0_0.csv",
    "Place": STATIC_ROOT / "place_0_0.csv",
    "Tag": STATIC_ROOT / "tag_0_0.csv",
    "Tagclass": STATIC_ROOT / "tagclass_0_0.csv",
}

EDGE_SPECS: list[EdgeSpec] = [
    EdgeSpec(DYNAMIC_ROOT / "forum_containerOf_post_0_0.csv", "Forum", "containerOf", "Post"),
    EdgeSpec(DYNAMIC_ROOT / "comment_hasCreator_person_0_0.csv", "Comment", "commentHasCreator", "Person"),
    EdgeSpec(DYNAMIC_ROOT / "post_hasCreator_person_0_0.csv", "Post", "postHasCreator", "Person"),
    EdgeSpec(DYNAMIC_ROOT / "person_hasInterest_tag_0_0.csv", "Person", "hasInterest", "Tag"),
    EdgeSpec(DYNAMIC_ROOT / "forum_hasMember_person_0_0.csv", "Forum", "hasMember", "Person"),
    EdgeSpec(DYNAMIC_ROOT / "forum_hasModerator_person_0_0.csv", "Forum", "hasModerator", "Person"),
    EdgeSpec(DYNAMIC_ROOT / "comment_hasTag_tag_0_0.csv", "Comment", "commentHasTag", "Tag"),
    EdgeSpec(DYNAMIC_ROOT / "forum_hasTag_tag_0_0.csv", "Forum", "forumHasTag", "Tag"),
    EdgeSpec(DYNAMIC_ROOT / "post_hasTag_tag_0_0.csv", "Post", "postHasTag", "Tag"),
    EdgeSpec(STATIC_ROOT / "tag_hasType_tagclass_0_0.csv", "Tag", "hasType", "Tagclass"),
    EdgeSpec(DYNAMIC_ROOT / "comment_isLocatedIn_place_0_0.csv", "Comment", "commentIsLocatedIn", "Place"),
    EdgeSpec(STATIC_ROOT / "organisation_isLocatedIn_place_0_0.csv", "Organisation", "organisationIsLocatedIn", "Place"),
    EdgeSpec(DYNAMIC_ROOT / "person_isLocatedIn_place_0_0.csv", "Person", "personIsLocatedIn", "Place"),
    EdgeSpec(DYNAMIC_ROOT / "post_isLocatedIn_place_0_0.csv", "Post", "postIsLocatedIn", "Place"),
    EdgeSpec(STATIC_ROOT / "place_isPartOf_place_0_0.csv", "Place", "isPartOf", "Place"),
    EdgeSpec(STATIC_ROOT / "tagclass_isSubclassOf_tagclass_0_0.csv", "Tagclass", "isSubclassOf", "Tagclass"),
    EdgeSpec(DYNAMIC_ROOT / "person_knows_person_0_0.csv", "Person", "knows", "Person"),
    EdgeSpec(DYNAMIC_ROOT / "person_likes_comment_0_0.csv", "Person", "likeComment", "Comment"),
    EdgeSpec(DYNAMIC_ROOT / "person_likes_post_0_0.csv", "Person", "likePost", "Post"),
    EdgeSpec(DYNAMIC_ROOT / "comment_replyOf_comment_0_0.csv", "Comment", "replyOfComment", "Comment"),
    EdgeSpec(DYNAMIC_ROOT / "comment_replyOf_post_0_0.csv", "Comment", "replyOfPost", "Post"),
    EdgeSpec(DYNAMIC_ROOT / "person_studyAt_organisation_0_0.csv", "Person", "studyAt", "Organisation"),
    EdgeSpec(DYNAMIC_ROOT / "person_workAt_organisation_0_0.csv", "Person", "workAt", "Organisation"),
]

# Range indexes on properties with selective equality/range filters in
# query.py. Node IDs are indexed separately before ingestion because edge
# loading looks up both endpoints by ID.
SECONDARY_INDEXES: list[tuple[str, str]] = [
    ("Place", "name"),
    ("Tag", "name"),
    ("Tagclass", "name"),
    ("Organisation", "name"),
    ("Person", "firstName"),
    ("Person", "lastName"),
    ("Comment", "length"),
]


def _iter_batches(rows: list[JsonBlob], batch_size: int) -> Iterable[list[JsonBlob]]:
    for start in range(0, len(rows), batch_size):
        yield rows[start : start + batch_size]


def _load_csv(path: Path) -> pl.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    return pl.read_csv(path, separator="|")


def _node_rows(df: pl.DataFrame) -> list[JsonBlob]:
    return df.rename({"id": "ID"}).to_dicts()


def _edge_rows(df: pl.DataFrame) -> list[JsonBlob]:
    src_key, dst_key, *prop_keys = df.columns
    return [
        {
            "src": row[src_key],
            "dst": row[dst_key],
            "props": {key: row[key] for key in prop_keys},
        }
        for row in df.iter_rows(named=True)
    ]


def create_index(graph: Graph, label: str, prop: str) -> None:
    graph.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")


def wait_for_indexes(graph: Graph, poll_interval: float = 1.0) -> None:
    while True:
        result = graph.query("CALL db.indexes() YIELD status RETURN status")
        if all(status == "OPERATIONAL" for (status,) in result.result_set):
            return
        time.sleep(poll_interval)


def write_nodes(graph: Graph, batch_size: int) -> None:
    for label, path in NODE_FILES.items():
        rows = _node_rows(_load_csv(path))
        query = f"UNWIND $rows AS row CREATE (n:{label}) SET n = row"
        for batch in _iter_batches(rows, batch_size):
            graph.query(query, {"rows": batch})
        print(f"Loaded {len(rows)} nodes for label {label}")


def write_edges(graph: Graph, batch_size: int) -> None:
    for spec in EDGE_SPECS:
        rows = _edge_rows(_load_csv(spec.path))
        query = f"""
            UNWIND $rows AS row
            MATCH (src:{spec.src_label} {{ID: row.src}})
            MATCH (dst:{spec.dst_label} {{ID: row.dst}})
            CREATE (src)-[r:{spec.rel_type}]->(dst)
            SET r = row.props
        """
        for batch in _iter_batches(rows, batch_size):
            graph.query(query, {"rows": batch})
        print(f"Loaded {len(rows)} edges for {spec.rel_type}")


def print_counts(graph: Graph) -> None:
    (num_nodes,) = graph.query("MATCH (n) RETURN count(n)").result_set[0]
    (num_rels,) = graph.query("MATCH ()-[r]->() RETURN count(r)").result_set[0]
    print(f"Graph contains {num_nodes} nodes and {num_rels} relationships")


def main(batch_size: int) -> None:
    db = FalkorDB(host=FALKORDB_HOST, port=FALKORDB_PORT)
    if FALKORDB_GRAPH in db.list_graphs():
        db.select_graph(FALKORDB_GRAPH).delete()
    graph = db.select_graph(FALKORDB_GRAPH)

    for label in NODE_FILES:
        create_index(graph, label, "ID")
    wait_for_indexes(graph)

    nodes_start = time.perf_counter()
    write_nodes(graph, batch_size)
    print(f"Nodes loaded in {time.perf_counter() - nodes_start:.4f}s")

    edges_start = time.perf_counter()
    write_edges(graph, batch_size)
    print(f"Edges loaded in {time.perf_counter() - edges_start:.4f}s")

    indexes_start = time.perf_counter()
    for label, prop in SECONDARY_INDEXES:
        create_index(graph, label, prop)
    wait_for_indexes(graph)
    print(f"Secondary indexes built in {time.perf_counter() - indexes_start:.4f}s")

    print_counts(graph)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Build FalkorDB graph from files")
    parser.add_argument(
        "--batch_size",
        "-b",
        type=int,
        default=20_000,
        help="Batch size of rows to ingest at a time",
    )
    args = parser.parse_args()

    main(args.batch_size)
