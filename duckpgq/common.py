"""
Shared helpers for connecting to DuckDB with the DuckPGQ extension loaded.

The DuckPGQ community extension matching the installed `duckdb` Python package
is installed from the DuckDB community extension repository on first use.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

SCRIPT_ROOT = Path(__file__).resolve().parent
DB_NAME = "ldbc_snb_sf1.duckdb"
# Override to place the database file somewhere else
DB_PATH = Path(os.environ.get("DUCKPGQ_DB_PATH", SCRIPT_ROOT / DB_NAME))
PROPERTY_GRAPH_NAME = "snb"


def connect(db_path: Path | str = DB_PATH, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection and load DuckPGQ."""
    conn = duckdb.connect(str(db_path), read_only=read_only)
    load_duckpgq(conn)
    return conn


def load_duckpgq(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("INSTALL duckpgq FROM community;")
    conn.execute("LOAD duckpgq;")


def duckdb_version(conn: duckdb.DuckDBPyConnection) -> str:
    rows = conn.execute("PRAGMA version").fetchall()
    return f"{rows[0][0]} ({rows[0][1]})"


def duckpgq_version(conn: duckdb.DuckDBPyConnection) -> str:
    rows = conn.execute(
        "SELECT extension_version FROM duckdb_extensions() WHERE extension_name = 'duckpgq'"
    ).fetchall()
    return rows[0][0] if rows and rows[0][0] else "unknown"
