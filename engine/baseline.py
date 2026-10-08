"""Baseline Reconciliation Engine (Naive Fixed-Priority / First Non-Null)."""

import time
from typing import Any, Dict, List, Optional


class BaselineReconciliationEngine:
    """
    Intentionally simplistic baseline approach for comparative benchmarking.
    Strategy: First non-null value according to rigid hard-coded source order.
    Flaws:
    - Ignores verification status (may pick unverified over verified).
    - Ignores freshness / staleness (may pick 50-day-old stale value over yesterday's fresh value).
    - Incapable of detecting ambiguity ties safely (never routes to manual review).
    """

    DEFAULT_ORDER = ["ERP", "E-commerce", "Store Inventory", "Delivery Partner"]

    def __init__(self, priority_order: Optional[List[str]] = None):
        self.priority_order = priority_order or self.DEFAULT_ORDER

    def reconcile_field(
        self,
        entity_type: str,
        field_name: str,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        cand_map = {c.get("source"): c for c in candidates}
        
        winner = None
        winning_source = None
        for src in self.priority_order:
            cand = cand_map.get(src)
            if cand and cand.get("value") is not None and str(cand.get("value")).strip() not in ("", "None", "nan", "null", "Missing"):
                winner = cand.get("value")
                winning_source = src
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if winner is None:
            return {
                "winner": None,
                "winning_source": None,
                "confidence": 0.0,
                "status": "MISSING",
                "is_ambiguous": False,
                "reason": "No non-null values found.",
                "elapsed_ms": elapsed_ms
            }

        return {
            "winner": winner,
            "winning_source": winning_source,
            "confidence": 75.0, # Fixed naive confidence
            "status": "RESOLVED",
            "is_ambiguous": False,
            "reason": f"Selected first available value from {winning_source}.",
            "elapsed_ms": elapsed_ms
        }
