"""Change History and Lineage Tracking Service."""

from typing import Any, Dict, List, Optional
from database.database import execute_non_query, execute_query


class HistoryService:
    @staticmethod
    def record_change(
        record_type: str,
        business_id: str,
        organization_id: int,
        field_name: str,
        previous_value: Optional[str],
        new_value: Optional[str],
        winning_source: Optional[str],
        user: Optional[Dict[str, Any]],
        reason: str,
        reconciliation_case_id: Optional[int] = None
    ) -> int:
        """
        Record a master record field update in the immutable change history.
        """
        user_id = user.get("id") if user else None
        user_email = user.get("email") if user else "SYSTEM"

        sql = """
        INSERT INTO change_history (
            record_type, business_id, organization_id, field_name,
            previous_value, new_value, winning_source, user_id, user_email,
            reason, reconciliation_case_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return execute_non_query(
            sql,
            (
                record_type, business_id, organization_id, field_name,
                str(previous_value) if previous_value is not None else None,
                str(new_value) if new_value is not None else None,
                winning_source, user_id, user_email, reason, reconciliation_case_id
            )
        )

    @staticmethod
    def get_change_history(
        user: Dict[str, Any],
        record_type: Optional[str] = None,
        business_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve change history with organization security isolation.
        """
        params: List[Any] = []
        conditions = ["1=1"]

        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            conditions.append("ch.organization_id = ?")
            params.append(user.get("organization_id"))

        if record_type and record_type != "All Types":
            conditions.append("ch.record_type = ?")
            params.append(record_type)

        if business_id and business_id.strip():
            conditions.append("ch.business_id LIKE ?")
            params.append(f"%{business_id.strip()}%")

        params.append(limit)
        where_clause = " AND ".join(conditions)

        sql = f"""
        SELECT ch.*, o.name as organization_name, rc.case_number
        FROM change_history ch
        LEFT JOIN organizations o ON ch.organization_id = o.id
        LEFT JOIN reconciliation_cases rc ON ch.reconciliation_case_id = rc.id
        WHERE {where_clause}
        ORDER BY ch.created_at DESC
        LIMIT ?
        """
        rows = execute_query(sql, tuple(params))
        return [dict(r) for r in rows]
