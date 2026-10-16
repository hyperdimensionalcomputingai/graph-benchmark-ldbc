"""
Build a DuckDB database with a DuckPGQ property graph of the LDBC SNB SF1 data.

The LDBC CSV files (pipe-delimited, with a header row) under `../csv` are read
into plain DuckDB tables with the same schema as the other engines in this
repository. Edge tables use `src`/`dst` for the endpoint IDs. A SQL/PGQ property
graph is then declared on top of the tables so that they can be queried with
`GRAPH_TABLE (... MATCH ...)` via DuckPGQ.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from common import DB_PATH, PROPERTY_GRAPH_NAME, connect, duckdb_version, duckpgq_version

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_ROOT = REPO_ROOT / "csv"
DYNAMIC = CSV_ROOT / "dynamic"
STATIC = CSV_ROOT / "static"


@dataclass(frozen=True)
class NodeTable:
    name: str
    path: Path
    # (column name, DuckDB type) in CSV order
    columns: list[tuple[str, str]]


@dataclass(frozen=True)
class EdgeTable:
    name: str
    path: Path
    src_table: str
    dst_table: str
    # Extra edge properties after the two endpoint IDs, in CSV order
    properties: list[tuple[str, str]] = field(default_factory=list)


NODE_TABLES: list[NodeTable] = [
    NodeTable(
        "Comment",
        DYNAMIC / "comment_0_0.csv",
        [
            ("id", "BIGINT"),
            ("creationDate", "TIMESTAMP"),
            ("locationIP", "VARCHAR"),
            ("browserUsed", "VARCHAR"),
            ("content", "VARCHAR"),
            ("length", "BIGINT"),
        ],
    ),
    NodeTable(
        "Forum",
        DYNAMIC / "forum_0_0.csv",
        [("id", "BIGINT"), ("title", "VARCHAR"), ("creationDate", "TIMESTAMP")],
    ),
    NodeTable(
        "Organisation",
        STATIC / "organisation_0_0.csv",
        [("id", "BIGINT"), ("type", "VARCHAR"), ("name", "VARCHAR"), ("url", "VARCHAR")],
    ),
    NodeTable(
        "Person",
        DYNAMIC / "person_0_0.csv",
        [
            ("id", "BIGINT"),
            ("firstName", "VARCHAR"),
            ("lastName", "VARCHAR"),
            ("gender", "VARCHAR"),
            ("birthday", "DATE"),
            ("creationDate", "TIMESTAMP"),
            ("locationIP", "VARCHAR"),
            ("browserUsed", "VARCHAR"),
        ],
    ),
    NodeTable(
        "Place",
        STATIC / "place_0_0.csv",
        [("id", "BIGINT"), ("name", "VARCHAR"), ("url", "VARCHAR"), ("type", "VARCHAR")],
    ),
    NodeTable(
        "Post",
        DYNAMIC / "post_0_0.csv",
        [
            ("id", "BIGINT"),
            ("imageFile", "VARCHAR"),
            ("creationDate", "TIMESTAMP"),
            ("locationIP", "VARCHAR"),
            ("browserUsed", "VARCHAR"),
            ("language", "VARCHAR"),
            ("content", "VARCHAR"),
            ("length", "BIGINT"),
        ],
    ),
    NodeTable(
        "Tag",
        STATIC / "tag_0_0.csv",
        [("id", "BIGINT"), ("name", "VARCHAR"), ("url", "VARCHAR")],
    ),
    NodeTable(
        "Tagclass",
        STATIC / "tagclass_0_0.csv",
        [("id", "BIGINT"), ("name", "VARCHAR"), ("url", "VARCHAR")],
    ),
]

EDGE_TABLES: list[EdgeTable] = [
    EdgeTable("containerOf", DYNAMIC / "forum_containerOf_post_0_0.csv", "Forum", "Post"),
    EdgeTable("commentHasCreator", DYNAMIC / "comment_hasCreator_person_0_0.csv", "Comment", "Person"),
    EdgeTable("postHasCreator", DYNAMIC / "post_hasCreator_person_0_0.csv", "Post", "Person"),
    EdgeTable("hasInterest", DYNAMIC / "person_hasInterest_tag_0_0.csv", "Person", "Tag"),
    EdgeTable(
        "hasMember",
        DYNAMIC / "forum_hasMember_person_0_0.csv",
        "Forum",
        "Person",
        [("joinDate", "TIMESTAMP")],
    ),
    EdgeTable("hasModerator", DYNAMIC / "forum_hasModerator_person_0_0.csv", "Forum", "Person"),
    EdgeTable("commentHasTag", DYNAMIC / "comment_hasTag_tag_0_0.csv", "Comment", "Tag"),
    EdgeTable("forumHasTag", DYNAMIC / "forum_hasTag_tag_0_0.csv", "Forum", "Tag"),
    EdgeTable("postHasTag", DYNAMIC / "post_hasTag_tag_0_0.csv", "Post", "Tag"),
    EdgeTable("hasType", STATIC / "tag_hasType_tagclass_0_0.csv", "Tag", "Tagclass"),
    EdgeTable("commentIsLocatedIn", DYNAMIC / "comment_isLocatedIn_place_0_0.csv", "Comment", "Place"),
    EdgeTable(
        "organisationIsLocatedIn",
        STATIC / "organisation_isLocatedIn_place_0_0.csv",
        "Organisation",
        "Place",
    ),
    EdgeTable("personIsLocatedIn", DYNAMIC / "person_isLocatedIn_place_0_0.csv", "Person", "Place"),
    EdgeTable("postIsLocatedIn", DYNAMIC / "post_isLocatedIn_place_0_0.csv", "Post", "Place"),
    EdgeTable("isPartOf", STATIC / "place_isPartOf_place_0_0.csv", "Place", "Place"),
    EdgeTable("isSubclassOf", STATIC / "tagclass_isSubclassOf_tagclass_0_0.csv", "Tagclass", "Tagclass"),
    EdgeTable(
        "knows",
        DYNAMIC / "person_knows_person_0_0.csv",
        "Person",
        "Person",
        [("creationDate", "TIMESTAMP")],
    ),
    EdgeTable(
        "likeComment",
        DYNAMIC / "person_likes_comment_0_0.csv",
        "Person",
        "Comment",
        [("creationDate", "TIMESTAMP")],
    ),
    EdgeTable(
        "likePost",
        DYNAMIC / "person_likes_post_0_0.csv",
        "Person",
        "Post",
        [("creationDate", "TIMESTAMP")],
    ),
    EdgeTable("replyOfComment", DYNAMIC / "comment_replyOf_comment_0_0.csv", "Comment", "Comment"),
    EdgeTable("replyOfPost", DYNAMIC / "comment_replyOf_post_0_0.csv", "Comment", "Post"),
    EdgeTable(
        "studyAt",
        DYNAMIC / "person_studyAt_organisation_0_0.csv",
        "Person",
        "Organisation",
        [("classYear", "BIGINT")],
    ),
    EdgeTable(
        "workAt",
        DYNAMIC / "person_workAt_organisation_0_0.csv",
        "Person",
        "Organisation",
        [("workFrom", "BIGINT")],
    ),
]

# (node table, column) pairs with selective equality filters in query.py. These
# mirror the ART secondary indexes created for Ladybug (ladybugdb/build_graph.py)
# and the BTREE scalar indexes for Lance Graph. DuckDB uses an ART index for a
# scan only for `=`/`IN` predicates that are expected to match few rows; range
# and CONTAINS predicates always go through the (zone-map pruned) table scan.
SECONDARY_INDEXES: list[tuple[str, str]] = [
    ("Place", "name"),  # Q1, Q9, Q12, Q16, Q24, Q27, Q28: pl.name = ...
    ("Tag", "name"),  # Q1, Q7, Q10, Q18, Q23, Q24, Q26, Q27: t.name = ...
    ("Person", "firstName"),  # Q2, Q13, Q25, Q29: p.firstName = ...
    ("Person", "lastName"),  # Q9, Q23 (+ Q4, Q13, Q25, Q29): p.lastName = ...
    ("Person", "birthday"),  # Q8: p.birthday > DATE ...
    ("Comment", "length"),  # Q4, Q20: c.length > ...
]


def _read_csv(path: Path, names: list[str]) -> str:
    """read_csv() call reading every column as VARCHAR; casts happen in the SELECT."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing CSV: {path}. Run download_dataset.py first.")
    name_list = ", ".join(f"'{n}'" for n in names)
    return (
        f"read_csv('{path}', delim='|', header=true, quote='', escape='', "
        f"all_varchar=true, names=[{name_list}])"
    )


def create_node_tables(conn: duckdb.DuckDBPyConnection) -> None:
    for table in NODE_TABLES:
        start = time.perf_counter()
        col_defs = ", ".join(
            f"{name} {ctype}{' PRIMARY KEY' if name == 'id' else ''}" for name, ctype in table.columns
        )
        selects = ", ".join(f"{name}::{ctype} AS {name}" for name, ctype in table.columns)
        names = [name for name, _ in table.columns]
        conn.execute(f"CREATE TABLE {table.name} ({col_defs});")
        conn.execute(f"INSERT INTO {table.name} SELECT {selects} FROM {_read_csv(table.path, names)};")
        count = conn.execute(f"SELECT count(*) FROM {table.name}").fetchall()[0][0]
        print(f"  {table.name:<24} {count:>10,} rows  ({time.perf_counter() - start:.2f}s)")


def create_edge_tables(conn: duckdb.DuckDBPyConnection) -> None:
    for table in EDGE_TABLES:
        start = time.perf_counter()
        columns = [("src", "BIGINT"), ("dst", "BIGINT"), *table.properties]
        col_defs = ", ".join(f"{name} {ctype}" for name, ctype in columns)
        selects = ", ".join(f"{name}::{ctype} AS {name}" for name, ctype in columns)
        names = [name for name, _ in columns]
        conn.execute(f"CREATE TABLE {table.name} ({col_defs});")
        conn.execute(f"INSERT INTO {table.name} SELECT {selects} FROM {_read_csv(table.path, names)};")
        count = conn.execute(f"SELECT count(*) FROM {table.name}").fetchall()[0][0]
        print(f"  {table.name:<24} {count:>10,} rows  ({time.perf_counter() - start:.2f}s)")


def create_secondary_indexes(conn: duckdb.DuckDBPyConnection) -> None:
    for table, column in SECONDARY_INDEXES:
        idx_name = f"{table}_{column}_idx"
        conn.execute(f"CREATE INDEX {idx_name} ON {table} ({column});")
        print(f"  Created index {idx_name} ON {table}({column})")


def property_graph_ddl() -> str:
    vertex_defs = ",\n".join(f"        {t.name} LABEL {t.name}" for t in NODE_TABLES)
    edge_defs = ",\n".join(
        f"        {e.name}\n"
        f"            SOURCE KEY (src) REFERENCES {e.src_table} (id)\n"
        f"            DESTINATION KEY (dst) REFERENCES {e.dst_table} (id)\n"
        f"            LABEL {e.name}"
        for e in EDGE_TABLES
    )
    return (
        f"CREATE PROPERTY GRAPH {PROPERTY_GRAPH_NAME}\n"
        f"    VERTEX TABLES (\n{vertex_defs}\n    )\n"
        f"    EDGE TABLES (\n{edge_defs}\n    );"
    )


def create_property_graph(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(property_graph_ddl())


def main(conn: duckdb.DuckDBPyConnection) -> None:
    print(f"DuckDB {duckdb_version(conn)}, DuckPGQ {duckpgq_version(conn)}")

    print("Loading node tables:")
    start = time.perf_counter()
    create_node_tables(conn)
    print(f"Nodes loaded in {time.perf_counter() - start:.2f}s")

    print("Loading edge tables:")
    start = time.perf_counter()
    create_edge_tables(conn)
    print(f"Edges loaded in {time.perf_counter() - start:.2f}s")

    print("Creating secondary indexes:")
    start = time.perf_counter()
    create_secondary_indexes(conn)
    print(f"Indexes created in {time.perf_counter() - start:.2f}s")

    create_property_graph(conn)
    print(f"Created property graph '{PROPERTY_GRAPH_NAME}'")
    conn.execute("CHECKPOINT;")
    print(f"Database written to {DB_PATH}")


if __name__ == "__main__":
    if "--print-ddl" in sys.argv:
        print(property_graph_ddl())
        raise SystemExit(0)
    # Delete the database file each time to start from a clean slate
    DB_PATH.unlink(missing_ok=True)
    Path(f"{DB_PATH}.wal").unlink(missing_ok=True)
    with connect(DB_PATH) as CONNECTION:
        main(CONNECTION)
