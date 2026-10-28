"""
Unit and Integration Tests for Production PostgreSQL Persistence and Connection Pooling.
"""

import pytest
from database.postgres_pool import persistence_manager, PersistenceManager
from database.migration import check_database_readiness, get_sqlite_table_names
from database.database import get_db_connection, execute_query


def test_persistence_manager_initialization():
    """Verify that PersistenceManager initializes and reports backend telemetry."""
    info = persistence_manager.get_backend_info()
    assert "backend" in info
    assert "connection_pooling" in info
    assert info["min_connections"] >= 1
    assert info["max_connections"] >= 1
    assert info["pool_timeout_sec"] > 0
    assert info["pgbouncer_compatible"] is True


def test_database_readiness_diagnostics():
    """Verify system diagnostics check returns valid health indicators."""
    diag = check_database_readiness()
    assert "engine" in diag
    assert "connection_pooling" in diag
    assert "rds_aurora_ready" in diag
    assert diag["rds_aurora_ready"] is True
    assert diag["pgbouncer_compatible"] is True
    assert diag["customer_records"] >= 0


def test_sqlite_table_discovery():
    """Verify user tables can be discovered in SQLite database."""
    conn = get_db_connection()
    tables = get_sqlite_table_names(conn)
    conn.close()
    assert "customers" in tables
    assert "reconciliation_cases" in tables
    assert "audit_logs" in tables
    assert "probabilistic_linkage_pairs" in tables
    assert "streaming_cdc_events" in tables


def test_pooled_query_execution():
    """Verify query execution through persistence abstraction."""
    rows = persistence_manager.execute_query("SELECT COUNT(*) as cnt FROM organizations")
    assert len(rows) == 1
    assert rows[0]["cnt"] >= 1
