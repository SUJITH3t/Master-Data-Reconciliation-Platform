"""Master Reconciliation Orchestration Pipeline."""

import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from engine.matching import normalize_record, extract_entity_key
from engine.freshness import evaluate_freshness, parse_timestamp
from engine.survivorship import SurvivorshipEngine
from engine.confidence import calculate_confidence
from engine.explanation import generate_explanation


class ReconciliationPipeline:
    def __init__(self, config_path: str = "config/survivorship_rules.yaml"):
        self.survivorship_engine = SurvivorshipEngine(config_path)

    def process_entity_field(
        self,
        entity_type: str,
        business_id: str,
        field_name: str,
        source_records: List[Dict[str, Any]],
        current_master_value: Optional[Any] = None,
        reference_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Reconcile a single field across multiple source records for an entity.
        Each source_record in source_records:
        {
            "source_system": "ERP",
            "field_values": {"email": "old@example.com", ...},
            "verification_status": "Verified",
            "source_timestamp": "2026-09-01 10:00:00"
        }
        """
        start_time = time.perf_counter()

        # 1. Normalize and extract candidates
        candidates = []
        for rec in source_records:
            src = rec.get("source_system", "Unknown")
            fields = rec.get("field_values", {})
            norm_fields = normalize_record(entity_type, fields)
            raw_val = norm_fields.get(field_name)
            ver = rec.get("verification_status", "Unverified")
            ts = rec.get("source_timestamp")

            fresh_status, fresh_label, age_days = evaluate_freshness(
                raw_val, ts, reference_date=reference_date
            )

            candidates.append({
                "source": src,
                "value": raw_val,
                "verification_status": ver,
                "timestamp": ts,
                "age_days": age_days,
                "freshness_status": fresh_status,
                "freshness_label": fresh_label
            })

        # 2. Check for differences and issues
        valid_cands = [c for c in candidates if c["value"] is not None and str(c["value"]).strip() != ""]
        unique_vals = list(set(str(c["value"]) for c in valid_cands))
        
        issue_type = "None"
        if len(unique_vals) > 1:
            issue_type = "Conflict"
        elif len(valid_cands) < len(candidates) and len(valid_cands) > 0:
            issue_type = "Missing"
        elif any(c["freshness_status"] == "Stale" for c in valid_cands):
            issue_type = "Stale"
        elif len(set(c["verification_status"] for c in valid_cands)) > 1:
            issue_type = "Verification Mismatch"

        # 3. Apply survivorship rules
        eval_result = self.survivorship_engine.evaluate_field(
            entity_type=entity_type,
            field_name=field_name,
            candidates=candidates
        )

        winner = eval_result["winner"]
        winning_source = eval_result["winning_source"]
        is_ambiguous = eval_result["is_ambiguous"]
        is_unanimous = (eval_result["status"] == "UNANIMOUS")
        active_rules = eval_result.get("active_rules", [])

        # 4. Confidence scoring
        confidence, conf_tier, breakdown = calculate_confidence(
            winner=winner,
            winning_source=winning_source,
            candidates=candidates,
            is_ambiguous=is_ambiguous,
            is_unanimous=is_unanimous
        )

        # 5. Plain English Explanation
        explanation = generate_explanation(
            entity_type=entity_type,
            field_name=field_name,
            winner=winner,
            winning_source=winning_source,
            candidates=candidates,
            is_ambiguous=is_ambiguous,
            is_unanimous=is_unanimous,
            active_rules=active_rules
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        decision_status = "MANUAL_REVIEW" if is_ambiguous else "PENDING"
        if not valid_cands:
            decision_status = "FAILED"

        return {
            "entity_type": entity_type,
            "business_id": business_id,
            "field_name": field_name,
            "issue_type": issue_type,
            "recommended_value": winner,
            "winning_source": winning_source,
            "previous_value": current_master_value,
            "confidence": confidence,
            "confidence_tier": conf_tier,
            "confidence_breakdown": breakdown,
            "status": decision_status,
            "reason": eval_result.get("reason"),
            "explanation": explanation,
            "is_ambiguous": is_ambiguous,
            "candidates": candidates,
            "evidence": {
                "candidates": candidates,
                "scores": eval_result.get("scores", {}),
                "active_rules": active_rules,
                "confidence_breakdown": breakdown,
                "elapsed_ms": elapsed_ms
            },
            "elapsed_ms": elapsed_ms
        }
