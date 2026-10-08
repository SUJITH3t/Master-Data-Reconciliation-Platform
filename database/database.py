"""Database connection and transaction helper module."""

import os
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path
from database.schema import CREATE_TABLES_SQL

DB_PATH = os.environ.get("DATABASE_PATH", "master_data.db")


def get_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "master_data.db")


def get_db_connection() -> sqlite3.Connection:
    """Returns a sqlite3 connection with Row factory and foreign keys enabled."""
    conn = sqlite3.connect(get_db_path(), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force: bool = False):
    """Initializes the database schema if not already present."""
    db_file = Path(get_db_path())
    if force and db_file.exists():
        db_file.unlink()

    conn = get_db_connection()
    try:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    """Execute a read query and return rows."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def execute_non_query(query: str, params: tuple = ()) -> int:
    """Execute insert/update/delete and return lastrowid."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid or cursor.rowcount
    finally:
        conn.close()


def execute_transaction(queries: List[tuple]) -> bool:
    """Execute a list of (sql, params) in a single atomic transaction."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for sql, params in queries:
            cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
