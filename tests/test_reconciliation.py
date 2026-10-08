"""Test Master Reconciliation Pipeline."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from engine.reconciliation import ReconciliationPipeline


def test_critical_customer_email_conflict():
    """
    Critical Test Case (Section 66):
    ERP Email = old@example.com (Updated 10 days ago, Verified)
    E-commerce Email = new@example.com (Updated 2 days ago, Verified)
    Store Email = Missing (Updated Missing)
    Expected: new@example.com from E-commerce
    """
    pipeline = ReconciliationPipeline()
    ref_date = datetime(2026, 9, 1, 12, 0, 0)

    sources = [
        {
            "source_system": "ERP",
            "verification_status": "Verified",
            "source_timestamp": (ref_date - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "field_values": {"email": "old@example.com"}
        },
        {
            "source_system": "E-commerce",
            "verification_status": "Verified",
            "source_timestamp": (ref_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "field_values": {"email": "new@example.com"}
        },
        {
            "source_system": "Store Inventory",
            "verification_status": "Unverified",
            "source_timestamp": None,
            "field_values": {"email": ""}
        }
    ]

    res = pipeline.process_entity_field(
        entity_type="Customer",
        business_id="CUST-001",
        field_name="email",
        source_records=sources,
        reference_date=ref_date
    )

    assert res["recommended_value"] == "new@example.com", f"Expected new@example.com, got {res['recommended_value']}"
    assert res["winning_source"] == "E-commerce", f"Expected E-commerce, got {res['winning_source']}"
    assert res["confidence"] >= 90.0, f"Expected high confidence >= 90%, got {res['confidence']}"
    assert "e-commerce email was selected because" in res["explanation"].lower()
    assert "store" in res["explanation"].lower() and "does not contain" in res["explanation"].lower()


def test_unanimous_agreement():
    """All systems agree on the same value."""
    pipeline = ReconciliationPipeline()
    sources = [
        {"source_system": "ERP", "verification_status": "Verified", "source_timestamp": "2026-09-01 10:00:00", "field_values": {"phone": "9811122233"}},
        {"source_system": "E-commerce", "verification_status": "Verified", "source_timestamp": "2026-09-01 11:00:00", "field_values": {"phone": "9811122233"}},
        {"source_system": "Store Inventory", "verification_status": "Unverified", "source_timestamp": "2026-08-15 10:00:00", "field_values": {"phone": "9811122233"}}
    ]

    res = pipeline.process_entity_field("Customer", "CUST-005", "phone", sources)
    assert res["recommended_value"] == "9811122233"
    assert res["confidence"] >= 95.0
    assert "agree" in res["explanation"].lower()
