"""Test Validation Experiment and Benchmark Calculation."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.validation_service import ValidationService


def test_validation_benchmark_execution():
    res = ValidationService.run_benchmark()
    assert "baseline" in res
    assert "proposed" in res
    assert "targets" in res

    base = res["baseline"]
    prop = res["proposed"]

    assert prop["total_records"] >= 50
    assert prop["precision"] > base["precision"], "Proposed precision should outperform naive baseline"
    assert prop["false_positive_rate"] < base["false_positive_rate"], "Proposed FPR must be lower than naive baseline"
    assert prop["avg_processing_time_ms"] > 0.0
    assert prop["total_processing_time_s"] > 0.0
