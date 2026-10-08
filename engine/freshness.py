"""Freshness and timestamp evaluation engine."""

from datetime import datetime
from typing import Any, Optional, Tuple


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parse various timestamp formats into a datetime object."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    ts_str = str(ts).strip()
    if not ts_str or ts_str.lower() in ("none", "null", "nan", "missing"):
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def calculate_age_days(timestamp: Optional[datetime], reference_date: Optional[datetime] = None) -> Optional[float]:
    """Calculate the age in days relative to a reference date (default now)."""
    if timestamp is None:
        return None
    ref = reference_date or datetime.now()
    delta = ref - timestamp
    return max(0.0, delta.total_seconds() / 86400.0)


def evaluate_freshness(
    value: Any,
    timestamp: Any,
    threshold_days: int = 30,
    reference_date: Optional[datetime] = None
) -> Tuple[str, str, Optional[float]]:
    """
    Evaluates freshness of a specific field value.
    Returns:
        (freshness_status, display_label, age_days)
        freshness_status in ['Fresh', 'Stale', 'Missing']
    """
    if value is None or str(value).strip() in ("", "None", "nan", "null", "Missing"):
        return "Missing", "🔴 Missing", None

    parsed_ts = parse_timestamp(timestamp)
    if parsed_ts is None:
        return "Stale", "🟡 Stale (Unknown date)", None

    age_days = calculate_age_days(parsed_ts, reference_date=reference_date)
    if age_days is None:
        return "Stale", "🟡 Stale", None

    if age_days <= threshold_days:
        if age_days < 1:
            label = "🟢 Fresh (Today)"
        elif age_days < 2:
            label = "🟢 Fresh (1 day ago)"
        else:
            label = f"🟢 Fresh ({int(age_days)} days ago)"
        return "Fresh", label, age_days
    else:
        label = f"🟡 Stale ({int(age_days)} days ago)"
        return "Stale", label, age_days
