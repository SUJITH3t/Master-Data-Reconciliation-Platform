"""Dynamic Survivorship Rule Evaluation Engine."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_rules(config_path: str = "config/survivorship_rules.yaml") -> Dict[str, Any]:
    """Dynamically load YAML survivorship rules."""
    path = Path(config_path)
    if not path.exists():
        # Fallback default configuration if path not found
        return {
            "settings": {"freshness_threshold_days": 30},
            "source_priorities": {"ERP": 10, "E-commerce": 8, "Store Inventory": 6, "Delivery Partner": 5},
            "entities": {}
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_valid_field_value(field_name: str, value: Any) -> bool:
    """Validate data quality for specific fields."""
    if value is None:
        return False
    val_str = str(value).strip()
    if not val_str or val_str.lower() in ("none", "null", "nan", "missing", "n/a"):
        return False

    if field_name == "email":
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", val_str))
    elif field_name == "phone":
        digits = re.sub(r"\D", "", val_str)
        return len(digits) >= 10
    elif field_name == "price":
        try:
            p = float(val_str)
            return p >= 0.0
        except ValueError:
            return False
    elif field_name == "sku":
        return len(val_str) >= 3 and not val_str.startswith("TEMP")
    return True


class SurvivorshipEngine:
    def __init__(self, config_path: str = "config/survivorship_rules.yaml"):
        self.config_path = config_path
        self.config = load_rules(config_path)
        self.source_priorities = self.config.get("source_priorities", {
            "ERP": 10, "E-commerce": 8, "Store Inventory": 6, "Delivery Partner": 5
        })

    def reload(self):
        self.config = load_rules(self.config_path)
        self.source_priorities = self.config.get("source_priorities", {
            "ERP": 10, "E-commerce": 8, "Store Inventory": 6, "Delivery Partner": 5
        })

    def get_field_rule_config(self, entity_type: str, field_name: str) -> Dict[str, Any]:
        entities = self.config.get("entities", {})
        entity_conf = entities.get(entity_type, {})
        fields_conf = entity_conf.get("fields", {})
        return fields_conf.get(field_name, {
            "rules": ["non_null", "freshness", "source_priority"],
            "tie_breaker": "source_priority",
            "description": "Default freshness and priority survivorship rule."
        })

    def evaluate_field(
        self,
        entity_type: str,
        field_name: str,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate candidate values from multiple source systems.
        candidates list format:
        [
            {
                "source": "ERP",
                "value": "old@example.com",
                "verification_status": "Verified",
                "timestamp": datetime(...),
                "age_days": 10.0,
                "freshness_status": "Fresh"
            },
            ...
        ]
        """
        rule_conf = self.get_field_rule_config(entity_type, field_name)
        active_rules = rule_conf.get("rules", ["non_null", "freshness", "source_priority"])
        tie_breaker = rule_conf.get("tie_breaker", "source_priority")

        # 1. Filter out empty/null values first
        valid_candidates = []
        for c in candidates:
            val = c.get("value")
            if val is not None and str(val).strip() not in ("", "None", "nan", "null", "Missing"):
                valid_candidates.append(c)

        if not valid_candidates:
            return {
                "status": "MISSING",
                "winner": None,
                "winning_source": None,
                "is_ambiguous": False,
                "reason": "All participating systems report missing or empty values.",
                "scores": {},
                "active_rules": active_rules
            }

        # If all valid candidates agree on the exact same value
        unique_values = set(str(c.get("value")) for c in valid_candidates)
        if len(unique_values) == 1:
            best_cand = valid_candidates[0]
            return {
                "status": "UNANIMOUS",
                "winner": best_cand["value"],
                "winning_source": best_cand["source"],
                "is_ambiguous": False,
                "reason": "All source systems are in complete agreement.",
                "scores": {c["source"]: 100.0 for c in valid_candidates},
                "active_rules": active_rules
            }

        # 2. Score candidates progressively based on configured rules
        scores = {}
        for c in valid_candidates:
            score = 0.0
            src = c.get("source", "")
            val = c.get("value")
            ver = c.get("verification_status", "Unverified") == "Verified"
            age = c.get("age_days", 999.0) if c.get("age_days") is not None else 999.0

            # Rule: non_null / valid_value
            if "valid_value" in active_rules or "non_null" in active_rules:
                if is_valid_field_value(field_name, val):
                    score += 50.0

            # Rule: verified_value
            if "verified_value" in active_rules:
                if ver:
                    score += 100.0

            # Rule: erp_priority
            if "erp_priority" in active_rules:
                if src == "ERP":
                    score += 80.0

            # Rule: freshness (prefer newer, lower age_days)
            if "freshness" in active_rules:
                # Age 0-30 days gives up to 40 points, older drops off
                if age <= 30:
                    score += max(0.0, 40.0 - (age * 1.0))
                else:
                    score += max(0.0, 10.0 - (age * 0.1))

            # Rule: completeness (longer, richer strings)
            if "completeness" in active_rules:
                score += min(15.0, len(str(val).strip()) * 1.0)

            # Rule: source_priority fallback weight
            if "source_priority" in active_rules:
                score += float(self.source_priorities.get(src, 1))

            scores[src] = round(score, 2)

        # Find maximum score
        max_score = max(scores.values())
        top_sources = [src for src, sc in scores.items() if sc == max_score]
        top_candidates = [c for c in valid_candidates if c["source"] in top_sources]

        # Check if top candidates have different values
        top_unique_vals = set(str(c["value"]) for c in top_candidates)

        # Ambiguity check
        if len(top_unique_vals) > 1:
            # Try tie_breaker
            if tie_breaker == "erp_priority":
                erp_cand = next((c for c in top_candidates if c["source"] == "ERP"), None)
                if erp_cand:
                    return {
                        "status": "RESOLVED",
                        "winner": erp_cand["value"],
                        "winning_source": erp_cand["source"],
                        "is_ambiguous": False,
                        "reason": "Tie resolved using ERP source authority.",
                        "scores": scores,
                        "active_rules": active_rules
                    }
            elif tie_breaker == "source_priority":
                # Highest source priority wins
                sorted_by_priority = sorted(
                    top_candidates,
                    key=lambda c: self.source_priorities.get(c["source"], 0),
                    reverse=True
                )
                if self.source_priorities.get(sorted_by_priority[0]["source"], 0) > self.source_priorities.get(sorted_by_priority[1]["source"], 0):
                    winner = sorted_by_priority[0]
                    return {
                        "status": "RESOLVED",
                        "winner": winner["value"],
                        "winning_source": winner["source"],
                        "is_ambiguous": False,
                        "reason": f"Tie resolved by source priority: {winner['source']} preferred.",
                        "scores": scores,
                        "active_rules": active_rules
                    }

            # If tie breaker is manual_review or still cannot safely break the tie:
            return {
                "status": "MANUAL_REVIEW",
                "winner": None,
                "winning_source": None,
                "is_ambiguous": True,
                "reason": "⚠️ Human review required: The available information is equally valid and the configured rules cannot safely determine a winner.",
                "scores": scores,
                "active_rules": active_rules
            }

        # Single clear winner
        winning_cand = top_candidates[0]
        return {
            "status": "RESOLVED",
            "winner": winning_cand["value"],
            "winning_source": winning_cand["source"],
            "is_ambiguous": False,
            "reason": f"Selected value from {winning_cand['source']} based on rules ({', '.join(active_rules)}).",
            "scores": scores,
            "active_rules": active_rules
        }
