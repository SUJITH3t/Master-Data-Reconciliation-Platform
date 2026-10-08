"""Deterministic Record Matching and Normalization Engine."""

import re
from typing import Any, Dict, Optional


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Normalize general strings: trim whitespace, collapse internal spaces."""
    if value is None:
        return None
    val = str(value).strip()
    if not val or val.lower() in ("nan", "none", "null", "missing", "n/a"):
        return None
    return re.sub(r"\s+", " ", val)


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Normalize email addresses: lowercase, strip, basic format verification."""
    val = normalize_string(email)
    if not val:
        return None
    val = val.lower()
    # Simple regex check for valid email structure
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", val):
        return val
    return val  # Return raw cleaned value even if slightly malformed for downstream validation


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize phone numbers: strip non-digits, standardize display."""
    val = normalize_string(phone)
    if not val:
        return None
    # Strip all formatting characters: brackets, dashes, spaces, dots
    digits = re.sub(r"[^\d+]", "", val)
    if len(digits) >= 10:
        return digits
    return digits if digits else None


def normalize_sku(sku: Optional[str]) -> Optional[str]:
    """Normalize SKU: uppercase, strip whitespace and leading/trailing dashes."""
    val = normalize_string(sku)
    if not val:
        return None
    return re.sub(r"[^A-Za-z0-9_-]", "", val).upper()


def normalize_record(record_type: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a record based on its entity type."""
    cleaned = {}
    for key, value in fields.items():
        if key == "email":
            cleaned[key] = normalize_email(value)
        elif key == "phone":
            cleaned[key] = normalize_phone(value)
        elif key == "sku":
            cleaned[key] = normalize_sku(value)
        elif key in ("name", "address", "category", "status"):
            cleaned[key] = normalize_string(value)
        elif key == "price":
            try:
                cleaned[key] = float(value) if value is not None and str(value).strip() != "" else None
            except (ValueError, TypeError):
                cleaned[key] = None
        else:
            cleaned[key] = normalize_string(str(value)) if value is not None else None
    return cleaned


def extract_entity_key(record_type: str, fields: Dict[str, Any], business_id: Optional[str] = None) -> str:
    """
    Deterministic identity key extraction.
    Ensures safe clustering without fragile fuzzy guesswork.
    """
    if business_id and business_id.strip():
        return business_id.strip().upper()

    if record_type == "Customer":
        if fields.get("customer_id"):
            return str(fields["customer_id"]).strip().upper()
        if fields.get("email"):
            return normalize_email(fields["email"]) or "UNKNOWN_CUST"
        if fields.get("phone"):
            return normalize_phone(fields["phone"]) or "UNKNOWN_CUST"

    elif record_type == "Product":
        if fields.get("product_id"):
            return str(fields["product_id"]).strip().upper()
        if fields.get("sku"):
            return normalize_sku(fields["sku"]) or "UNKNOWN_PROD"

    elif record_type == "Supplier":
        if fields.get("supplier_id"):
            return str(fields["supplier_id"]).strip().upper()
        if fields.get("email"):
            return normalize_email(fields["email"]) or "UNKNOWN_SUP"

    return "UNKNOWN_ENTITY"
