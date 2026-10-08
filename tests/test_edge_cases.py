"""Test Master Data Edge Cases and Ambiguity Safety."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from engine.reconciliation import ReconciliationPipeline
from services.validation_service import ValidationService


def test_ambiguous_verified_email_tie():
    """
    Critical Ambiguous Test Case (Section 67):
    ERP Email = a@example.com, Verified, Updated 2 days ago
    E-commerce Email = b@example.com, Verified, Updated 2 days ago
    Expected: MANUAL_REVIEW (Never select randomly)
    """
    pipeline = ReconciliationPipeline()
    ref_date = datetime(2026, 9, 1, 12, 0, 0)
    ts = (ref_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    sources = [
        {"source_system": "ERP", "verification_status": "Verified", "source_timestamp": ts, "field_values": {"email": "a@example.com"}},
        {"source_system": "E-commerce", "verification_status": "Verified", "source_timestamp": ts, "field_values": {"email": "b@example.com"}}
    ]

    res = pipeline.process_entity_field("Customer", "CUST-EDGE", "email", sources, reference_date=ref_date)
    assert res["status"] == "MANUAL_REVIEW", f"Expected MANUAL_REVIEW, got {res['status']}"
    assert res["is_ambiguous"] is True
    assert "human review required" in res["explanation"].lower()


def test_stale_preserved_over_missing():
    """A stale verified record (90 days old) must not be replaced by a blank missing record."""
    pipeline = ReconciliationPipeline()
    res = ValidationService.run_edge_case_test(2)
    assert res["passed"] is True
    assert res["actual"] == "historical@corp.com"


def test_edge_case_interactive_demonstrators():
    for case_num in (1, 2, 3):
        res = ValidationService.run_edge_case_test(case_num)
        assert res["passed"] is True, f"Edge case {case_num} failed: {res}"
