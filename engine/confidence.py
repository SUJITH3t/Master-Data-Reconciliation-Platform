"""Confidence scoring engine based on decision evidence."""

from typing import Any, Dict, List, Optional, Tuple


def calculate_confidence(
    winner: Any,
    winning_source: Optional[str],
    candidates: List[Dict[str, Any]],
    is_ambiguous: bool = False,
    is_unanimous: bool = False
) -> Tuple[float, str, Dict[str, Any]]:
    """
    Calculates deterministic confidence score between 0.0% and 100.0%.
    Factors:
    - Verification status (+35%)
    - Freshness status (+25%)
    - Source priority/authority (+18%)
    - Multi-system agreement (+12%)
    - Value formatting completeness (+10%)
    - Ambiguity penalty (-50%)

    Returns:
        (score, tier_label, breakdown_dict)
    """
    if is_ambiguous or winner is None or winning_source is None:
        return 40.0, "Low", {
            "verification": 0.0,
            "freshness": 0.0,
            "source_authority": 0.0,
            "agreement": 0.0,
            "completeness": 0.0,
            "penalty": -50.0,
            "tier": "Low"
        }

    if is_unanimous:
        return 98.0, "High", {
            "verification": 35.0,
            "freshness": 25.0,
            "source_authority": 18.0,
            "agreement": 12.0,
            "completeness": 8.0,
            "penalty": 0.0,
            "tier": "High"
        }

    # Find winning candidate
    winner_cand = next((c for c in candidates if c.get("source") == winning_source), None)
    if not winner_cand:
        return 50.0, "Low", {"tier": "Low"}

    # 1. Verification score (up to 35)
    ver_score = 35.0 if winner_cand.get("verification_status") == "Verified" else 10.0

    # 2. Freshness score (up to 25)
    age = winner_cand.get("age_days")
    if age is not None:
        if age <= 3:
            fresh_score = 25.0
        elif age <= 10:
            fresh_score = 22.0
        elif age <= 30:
            fresh_score = 18.0
        elif age <= 60:
            fresh_score = 10.0
        else:
            fresh_score = 5.0
    else:
        fresh_score = 5.0

    # 3. Source Authority (up to 18)
    src_prio = {"ERP": 18.0, "E-commerce": 17.0, "Store Inventory": 14.0, "Delivery Partner": 13.0}
    auth_score = src_prio.get(winning_source, 10.0)

    # 4. Multi-system agreement (up to 12)
    valid_cands = [c for c in candidates if c.get("value") is not None and str(c.get("value")).strip() != ""]
    agreeing = [c for c in valid_cands if str(c.get("value")) == str(winner)]
    if len(valid_cands) > 1:
        agree_ratio = len(agreeing) / len(valid_cands)
        agree_score = round(agree_ratio * 12.0, 1)
    else:
        agree_score = 8.0

    # 5. Completeness / validity (up to 10)
    comp_score = 10.0 if len(str(winner).strip()) > 3 else 5.0

    total = round(ver_score + fresh_score + auth_score + agree_score + comp_score, 1)
    total = max(10.0, min(99.0, total))

    if total >= 90.0:
        tier = "High"
    elif total >= 70.0:
        tier = "Medium"
    else:
        tier = "Low"

    breakdown = {
        "verification": ver_score,
        "freshness": fresh_score,
        "source_authority": auth_score,
        "agreement": agree_score,
        "completeness": comp_score,
        "penalty": 0.0,
        "tier": tier
    }
    return total, tier, breakdown
