"""
Unit and Integration Tests for W3C PROV-O Lineage Tracking and Erlang-C Reviewer Capacity Analysis.
"""

import pytest
from services.lineage_service import LineageService, ProvenanceNodeType
from services.capacity_analysis import CapacityAnalysisEngine


def test_w3c_provo_lineage_graph_generation():
    """Verify W3C PROV-O provenance DAG construction for an existing master record."""
    prov = LineageService.get_entity_provenance("Customer", "CUST-001")
    assert prov["business_id"] == "CUST-001"
    assert prov["record_type"] == "Customer"
    assert "graph" in prov
    assert len(prov["graph"]["nodes"]) >= 1

    # Check for presence of golden master node
    golden_node = next((n for n in prov["graph"]["nodes"] if n["type"] == ProvenanceNodeType.GOLDEN_MASTER), None)
    assert golden_node is not None
    assert golden_node["prov_type"] == "prov:Entity"


def test_erlang_c_queuing_stability_condition():
    """Verify Erlang-C calculations enforce stability and output bounded wait times."""
    # Test typical mid-market retail workload
    res = CapacityAnalysisEngine.evaluate_capacity(
        daily_ingestion_volume=50000,
        manual_review_rate=0.10,
        operating_hours_per_day=8.0,
        average_handle_time_sec=120.0,
        target_sla_minutes=15.0
    )
    assert res["daily_review_cases"] == 5000
    assert res["recommended_active_reviewers"] >= res["min_theoretical_servers"]
    assert res["required_gross_fte"] >= res["recommended_active_reviewers"]
    assert res["utilization_pct"] < 100.0  # System is stable
    assert res["sla_compliance_pct"] >= 90.0


def test_erlang_c_matrix_generation():
    """Verify enterprise workload scaling matrix calculates all retail tiers."""
    matrix = CapacityAnalysisEngine.generate_capacity_matrix()
    assert len(matrix) == 4
    for tier in matrix:
        assert tier["daily_ingestion_volume"] > 0
        assert tier["required_gross_fte"] > 0
        assert tier["sla_compliance_pct"] >= 90.0
