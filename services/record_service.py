"""Master Record and Source Record Management Service with Data Isolation."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from database.database import execute_query, execute_non_query, execute_transaction
from services.auth_service import AuthService


class RecordService:
    @staticmethod
    def get_master_records(
        entity_type: str,
        user: Dict[str, Any],
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch master records (Customer, Product, Supplier) with strict organization isolation.
        """
        table_map = {
            "Customer": "customers",
            "Product": "products",
            "Supplier": "suppliers"
        }
        table = table_map.get(entity_type, "customers")
        
        conditions = ["1=1"]
        params: List[Any] = []

        # Enforce Org-Level Isolation:
        # Non-Admins only see records in their organization
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            conditions.append(f"{table}.organization_id = ?")
            params.append(user.get("organization_id"))

        if search and search.strip():
            sq = f"%{search.strip()}%"
            if entity_type == "Customer":
                conditions.append(f"({table}.business_id LIKE ? OR {table}.name LIKE ? OR {table}.email LIKE ? OR {table}.phone LIKE ?)")
                params.extend([sq, sq, sq, sq])
            elif entity_type == "Product":
                conditions.append(f"({table}.business_id LIKE ? OR {table}.name LIKE ? OR {table}.sku LIKE ? OR {table}.category LIKE ?)")
                params.extend([sq, sq, sq, sq])
            elif entity_type == "Supplier":
                conditions.append(f"({table}.business_id LIKE ? OR {table}.name LIKE ? OR {table}.email LIKE ? OR {table}.phone LIKE ?)")
                params.extend([sq, sq, sq, sq])

        params.append(limit)
        where_clause = " AND ".join(conditions)

        sql = f"""
        SELECT {table}.*, o.name as organization_name, o.code as organization_code
        FROM {table}
        JOIN organizations o ON {table}.organization_id = o.id
        WHERE {where_clause}
        ORDER BY {table}.updated_at DESC
        LIMIT ?
        """
        rows = execute_query(sql, tuple(params))
        return [dict(r) for r in rows]

    @staticmethod
    def get_single_master_record(
        entity_type: str,
        business_id: str,
        user: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get single master record by business_id with authorization check."""
        table_map = {"Customer": "customers", "Product": "products", "Supplier": "suppliers"}
        table = table_map.get(entity_type, "customers")

        sql = f"""
        SELECT {table}.*, o.name as organization_name
        FROM {table}
        JOIN organizations o ON {table}.organization_id = o.id
        WHERE {table}.business_id = ?
        """
        params = [business_id]
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            sql += f" AND {table}.organization_id = ?"
            params.append(user.get("organization_id"))

        rows = execute_query(sql, tuple(params))
        return dict(rows[0]) if rows else None

    @staticmethod
    def get_source_records_for_entity(
        entity_type: str,
        business_id: str,
        user: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch all source system records for a given entity."""
        conditions = ["record_type = ?", "business_identifier = ?"]
        params: List[Any] = [entity_type, business_id]

        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            conditions.append("organization_id = ?")
            params.append(user.get("organization_id"))

        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT sr.*, o.name as organization_name
        FROM source_records sr
        JOIN organizations o ON sr.organization_id = o.id
        WHERE {where_clause}
        ORDER BY sr.source_timestamp DESC
        """
        rows = execute_query(sql, tuple(params))
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["field_values"] = json.loads(d["field_values_json"])
            except Exception:
                d["field_values"] = {}
            results.append(d)
        return results

    @staticmethod
    def ingest_source_record(
        record_type: str,
        organization_id: int,
        source_system: str,
        business_identifier: str,
        field_values: Dict[str, Any],
        verification_status: str = "Unverified",
        source_timestamp: Optional[str] = None
    ) -> int:
        """Insert a newly ingested source record."""
        ts = source_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO source_records (
            record_type, organization_id, source_system,
            business_identifier, field_values_json, verification_status, source_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return execute_non_query(
            sql,
            (record_type, organization_id, source_system, business_identifier, json.dumps(field_values), verification_status, ts)
        )

    @staticmethod
    def update_master_field(
        entity_type: str,
        business_id: str,
        organization_id: int,
        field_name: str,
        new_value: Any
    ) -> bool:
        """Update a field on the master entity."""
        table_map = {"Customer": "customers", "Product": "products", "Supplier": "suppliers"}
        table = table_map.get(entity_type, "customers")

        # Allowable column check to prevent SQL injection
        allowed_columns = {
            "Customer": ["name", "email", "phone", "address", "verification_status", "status"],
            "Product": ["sku", "name", "price", "category", "status"],
            "Supplier": ["name", "email", "phone", "address", "status", "verification_status"]
        }
        if field_name not in allowed_columns.get(entity_type, []):
            raise ValueError(f"Invalid field {field_name} for entity {entity_type}")

        sql = f"""
        UPDATE {table}
        SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP, last_reconciled_at = CURRENT_TIMESTAMP
        WHERE business_id = ? AND organization_id = ?
        """
        execute_non_query(sql, (new_value, business_id, organization_id))
        return True
