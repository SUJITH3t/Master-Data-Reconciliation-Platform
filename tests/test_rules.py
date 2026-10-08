"""Test Dynamic Survivorship Rules."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.survivorship import SurvivorshipEngine, load_rules


def test_yaml_config_loading():
    rules = load_rules("config/survivorship_rules.yaml")
    assert "entities" in rules
    assert "Customer" in rules["entities"]
    assert "Product" in rules["entities"]
    assert "Supplier" in rules["entities"]


def test_erp_product_status_priority():
    """ERP product status has authoritative priority over newer e-commerce status."""
    engine = SurvivorshipEngine()
    candidates = [
        {"source": "ERP", "value": "Discontinued", "verification_status": "Verified", "age_days": 15.0},
        {"source": "E-commerce", "value": "Active", "verification_status": "Verified", "age_days": 1.0},
        {"source": "Store Inventory", "value": "In Stock", "verification_status": "Unverified", "age_days": 5.0}
    ]

    res = engine.evaluate_field("Product", "status", candidates)
    assert res["winner"] == "Discontinued"
    assert res["winning_source"] == "ERP"


def test_verified_supplier_priority():
    """Verified supplier info beats unverified even if unverified is newer."""
    engine = SurvivorshipEngine()
    candidates = [
        {"source": "ERP", "value": "unverified@supplier.com", "verification_status": "Unverified", "age_days": 1.0},
        {"source": "Delivery Partner", "value": "verified@supplier.com", "verification_status": "Verified", "age_days": 5.0}
    ]

    res = engine.evaluate_field("Supplier", "email", candidates)
    assert res["winner"] == "verified@supplier.com"
    assert res["winning_source"] == "Delivery Partner"
