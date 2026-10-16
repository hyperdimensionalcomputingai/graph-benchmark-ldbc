"""
Count the number of node/edge tables and the number of rows PER table in the
DuckDB database, to verify the graph against the counts in the root README.
"""

from __future__ import annotations

from build_graph import EDGE_TABLES, NODE_TABLES
from common import DB_PATH, connect


def main() -> None:
    with connect(DB_PATH) as conn:
        print(f"Node tables: {len(NODE_TABLES)}")
        print(f"Relationship tables: {len(EDGE_TABLES)}")

        total_nodes = 0
        print("\nNode counts:")
        for table in NODE_TABLES:
            count = conn.execute(f"SELECT count(*) FROM {table.name}").fetchall()[0][0]
            total_nodes += count
            print(f"- {table.name}: {count}")

        total_rels = 0
        print("\nRelationship counts:")
        for table in EDGE_TABLES:
            count = conn.execute(f"SELECT count(*) FROM {table.name}").fetchall()[0][0]
            total_rels += count
            print(f"- {table.name}: {count}")

        print("\nTotals:")
        print(f"- nodes: {total_nodes}")
        print(f"- relationships: {total_rels}")


if __name__ == "__main__":
    main()
