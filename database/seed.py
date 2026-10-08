import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
"""Database Seeder for Master Data Hub with Realistic Enterprise Demo Data."""

import csv
import json
from datetime import datetime, timedelta
from database.database import init_db, execute_non_query, execute_query
from services.auth_service import hash_password
from engine.reconciliation import ReconciliationPipeline


def seed_database(force: bool = False):
    """Seed all tables with users, orgs, sources, demo entities, and initial reconciliation cases."""
    init_db(force=force)

    # Check if already seeded
    existing_users = execute_query("SELECT COUNT(*) as cnt FROM users")
    if existing_users and existing_users[0]["cnt"] > 0 and not force:
        return

    print("Seeding Master Data Hub database...")

    # 1. Organizations
    orgs = [
        ("RET-HQ", "Retail Company", "Enterprise Headquarters & Master Catalog"),
        ("RET-STORE", "Store Network", "Physical Retail Store Outlets & Local Inventory"),
        ("LOG-PARTNER", "Delivery Partner", "External Third-Party Freight & Delivery Logistics")
    ]
    for code, name, desc in orgs:
        execute_non_query(
            "INSERT INTO organizations (code, name, description) VALUES (?, ?, ?)",
            (code, name, desc)
        )

    # 2. Source Systems
    sources = [
        ("ERP", "Enterprise Resource Planning (ERP)", 10, "status,sku,category", "Core SAP/Oracle transactional backbone", 1),
        ("E-commerce", "E-commerce Platform", 8, "email,phone,address", "Shopify/Magento digital customer storefront", 1),
        ("Store Inventory", "Store Point-of-Sale & Inventory", 6, "price,status", "Physical POS store terminals", 1),
        ("Delivery Partner", "Delivery Partner Logistics", 5, "address,tracking", "Third-party dispatch and freight tracking", 1),
    ]
    for code, name, prio, auth_f, desc, is_act in sources:
        execute_non_query(
            "INSERT INTO source_systems (code, name, priority_score, authoritative_fields, description, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            (code, name, prio, auth_f, desc, is_act)
        )

    # 3. Users (Documented demo credentials)
    users = [
        ("admin@retail.demo", hash_password("Admin123!"), "Sarah Jenkins (Admin)", "Admin", 1),
        ("specialist@retail.demo", hash_password("Spec123!"), "Marcus Vance (Recon Specialist)", "Reconciliation Specialist", 1),
        ("manager@retail.demo", hash_password("Store123!"), "Vikram Dave (Store Manager)", "Store Manager", 2),
        ("partner@delivery.demo", hash_password("Partner123!"), "Elena Rostova (Delivery Partner)", "External Partner", 3),
    ]
    for email, pwd_hash, full_name, role, org_id in users:
        execute_non_query(
            "INSERT INTO users (email, password_hash, full_name, role, organization_id, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (email, pwd_hash, full_name, role, org_id)
        )

    # 4. Ingest validation/demo dataset into source_records and initial master records
    dataset_path = "data/validation_dataset.csv"
    
    # Structure rows by (entity_type, business_id, organization, source_system)
    entity_records = {}
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["entity_type"], row["business_id"], row["organization"], row["source_system"])
            if key not in entity_records:
                entity_records[key] = {
                    "entity_type": row["entity_type"],
                    "business_id": row["business_id"],
                    "organization": row["organization"],
                    "source_system": row["source_system"],
                    "verification_status": row["verification_status"],
                    "timestamp": row["timestamp"],
                    "fields": {}
                }
            entity_records[key]["fields"][row["field_name"]] = row["field_value"]

    org_map = {"Retail Company": 1, "Store Network": 2, "Delivery Partner": 3}

    # Save to source_records table
    for (rec_type, bus_id, org_name, src_sys), data in entity_records.items():
        org_id = org_map.get(org_name, 1)
        execute_non_query(
            """
            INSERT INTO source_records (
                record_type, organization_id, source_system, business_identifier,
                field_values_json, verification_status, source_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec_type, org_id, src_sys, bus_id,
                json.dumps(data["fields"]), data["verification_status"], data["timestamp"]
            )
        )

    # Create initial baseline master records
    # Customers
    for i in range(1, 21):
        cid = f"CUST-{i:03d}"
        org_id = 2 if cid == "CUST-004" else 1
        execute_non_query(
            """
            INSERT OR IGNORE INTO customers (business_id, organization_id, name, email, phone, address, verification_status, data_quality_score, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Unverified', 85.0, 'Active')
            """,
            (cid, org_id, f"Customer {cid}", f"cust{i}@retail.demo", f"98000{i:05d}", f"Initial St, City {i}")
        )

    # Products
    for i in range(1, 16):
        pid = f"PROD-{i:03d}"
        execute_non_query(
            """
            INSERT OR IGNORE INTO products (business_id, organization_id, sku, name, price, category, status, data_quality_score)
            VALUES (?, 1, ?, ?, ?, 'Retail', 'Active', 90.0)
            """,
            (pid, f"SKU-{pid}", f"Master Product {pid}", 1000.0 * i)
        )

    # Suppliers
    for i in range(1, 16):
        sid = f"SUP-{i:03d}"
        org_id = 3 if sid in ("SUP-001", "SUP-002") else 1
        execute_non_query(
            """
            INSERT OR IGNORE INTO suppliers (business_id, organization_id, name, email, phone, address, status, verification_status, data_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, 'Active', 'Unverified', 88.0)
            """,
            (sid, org_id, f"Supplier Corp {sid}", f"orders@{sid.lower()}.com", "02224001122", "Industrial Terminal")
        )

    # 5. Pre-run reconciliation on the initial seeded data so the UI has rich live cases ready for demo
    pipeline = ReconciliationPipeline()
    sys_user = {"id": 1, "email": "admin@retail.demo", "role": "Admin", "organization_id": 1}

    # Group source records by entity
    entities_to_reconcile = [
        # Prominent demo cases:
        ("Customer", "CUST-001", 1, "email"),
        ("Customer", "CUST-002", 1, "email"),
        ("Customer", "CUST-003", 1, "email"),
        ("Customer", "CUST-004", 2, "phone"),
        ("Product", "PROD-001", 1, "price"),
        ("Product", "PROD-002", 1, "status"),
        ("Supplier", "SUP-001", 3, "email"),
        ("Supplier", "SUP-002", 3, "status"),
    ]

    for rec_type, bus_id, org_id, f_name in entities_to_reconcile:
        # Fetch matching source records
        s_rows = execute_query(
            "SELECT * FROM source_records WHERE record_type = ? AND business_identifier = ?",
            (rec_type, bus_id)
        )
        src_records = []
        for sr in s_rows:
            d = dict(sr)
            d["field_values"] = json.loads(d["field_values_json"])
            src_records.append(d)

        # Reconcile field
        res = pipeline.process_entity_field(
            entity_type=rec_type,
            business_id=bus_id,
            field_name=f_name,
            source_records=src_records,
            current_master_value="old@example.com" if f_name == "email" else "Original Value",
            reference_date=datetime(2026, 9, 1, 12, 0, 0)
        )

        case_num = f"REC-{rec_type[:3].upper()}-{bus_id}-{f_name.upper()}"
        execute_non_query(
            """
            INSERT OR REPLACE INTO reconciliation_cases (
                case_number, record_type, business_id, organization_id,
                field_name, issue_type, recommended_value, winning_source,
                previous_value, confidence_score, status, reason, explanation,
                evidence_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                case_num, rec_type, bus_id, org_id, f_name, res["issue_type"],
                str(res["recommended_value"]) if res["recommended_value"] is not None else None,
                res["winning_source"], res["previous_value"], res["confidence"],
                res["status"], res["reason"], res["explanation"], json.dumps(res["evidence"])
            )
        )

    # 6. Pre-seed initial audit logs demonstrating system readiness
    from services.audit_service import AuditService
    AuditService.log_event(
        action="SYSTEM_INITIALIZE",
        user=sys_user,
        record_type="SYSTEM",
        decision="SUCCESS",
        reason="Master Data Hub database initialized and seeded with 50 entities across 4 source systems.",
        organization_id=1
    )
    AuditService.log_event(
        action="INGEST_SOURCE_RECORDS",
        user=sys_user,
        record_type="ALL",
        decision="SUCCESS",
        reason="Ingested 690 source system records from ERP, E-commerce, Store Inventory, and Delivery Partner.",
        organization_id=1
    )

    print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_database(force=True)
