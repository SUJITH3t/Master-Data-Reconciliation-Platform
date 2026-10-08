"""Business-friendly plain English explanation generator."""

from typing import Any, Dict, List, Optional


def generate_explanation(
    entity_type: str,
    field_name: str,
    winner: Any,
    winning_source: Optional[str],
    candidates: List[Dict[str, Any]],
    is_ambiguous: bool = False,
    is_unanimous: bool = False,
    active_rules: Optional[List[str]] = None
) -> str:
    """
    Generates plain-English business explanation without technical jargon.
    """
    active_rules = active_rules or []
    
    # Missing case
    if not candidates or all(c.get("value") is None or str(c.get("value")).strip() == "" for c in candidates):
        return f"All participating systems report missing or empty values for {field_name}."

    # Ambiguous / Manual Review case
    if is_ambiguous or winning_source is None:
        verified_conflicts = [c["source"] for c in candidates if c.get("verification_status") == "Verified"]
        if len(verified_conflicts) >= 2:
            return (
                f"⚠️ Human review required: Multiple verified sources ({', '.join(verified_conflicts)}) "
                f"contain equally recent conflicting {field_name} values. The configured survivorship rules "
                f"cannot safely determine a single winner without human verification."
            )
        sources_with_data = [c["source"] for c in candidates if c.get("value")]
        return (
            f"⚠️ Human review required: Participating systems ({', '.join(sources_with_data)}) contain "
            f"conflicting {field_name} values of equal rule weight. A reconciliation specialist must verify the authoritative record."
        )

    # Unanimous agreement
    if is_unanimous or len(set(str(c.get("value")) for c in candidates if c.get("value"))) == 1:
        return f"All available business systems agree on the {field_name} value '{winner}'."

    # Finding winner and losing candidates
    winner_cand = next((c for c in candidates if c.get("source") == winning_source), None)
    losing_cands = [c for c in candidates if c.get("source") != winning_source]

    reasons = []
    
    # Specific rule drivers
    if "erp_priority" in active_rules and winning_source == "ERP":
        reasons.append("ERP is the configured authoritative enterprise system for this attribute")
    
    if winner_cand:
        if winner_cand.get("verification_status") == "Verified":
            unverified_losers = [c["source"] for c in losing_cands if c.get("verification_status") != "Verified" and c.get("value")]
            if unverified_losers:
                reasons.append(f"it is officially verified whereas {', '.join(unverified_losers)} is unverified")
            else:
                reasons.append("it is verified")
        
        age = winner_cand.get("age_days")
        if age is not None:
            older_losers = [c for c in losing_cands if c.get("age_days") is not None and c.get("age_days") > age and c.get("value")]
            if older_losers:
                older_names = [c["source"] for c in older_losers]
                reasons.append(f"it was updated more recently ({winner_cand.get('freshness_status', 'Fresh')}) than {', '.join(older_names)}")

    if not reasons:
        reasons.append(f"it aligns with the primary survivorship policy ({winning_source} source priority)")

    explanation = f"The {winning_source} {field_name} was selected because {' and '.join(reasons)}."

    # Mention missing sources
    missing_sources = [c["source"] for c in losing_cands if not c.get("value") or str(c.get("value")).strip() == ""]
    if missing_sources:
        explanation += f" The {' and '.join(missing_sources)} system does not contain a {field_name}."

    return explanation
