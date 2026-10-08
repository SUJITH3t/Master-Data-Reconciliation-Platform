"""Immutable Audit Logging Service."""

from typing import Any, Dict, List, Optional
from database.database import execute_non_query, execute_query


class AuditService:
    @staticmethod
    def log_event(
        action: str,
        user: Optional[Dict[str, Any]] = None,
        record_type: Optional[str] = None,
        business_id: Optional[str] = None,
        decision: Optional[str] = None,
        reason: Optional[str] = None,
        organization_id: Optional[int] = None,
        ip_address: str = "127.0.0.1"
    ) -> int:
        """
        Record an immutable audit log entry.
        """
        user_id = user.get("id") if user else None
        user_email = user.get("email") if user else "SYSTEM"
        role = user.get("role") if user else "System"
        org_id = organization_id or (user.get("organization_id") if user else 1)

        sql = """
        INSERT INTO audit_logs (
            user_id, user_email, role, organization_id, action,
            record_type, business_id, decision, reason, ip_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return execute_non_query(
            sql,
            (user_id, user_email, role, org_id, action, record_type, business_id, decision, reason, ip_address)
        )

    @staticmethod
    def get_audit_logs(
        user: Dict[str, Any],
        limit: int = 100,
        action_filter: Optional[str] = None,
        record_type_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with authorization filtering.
        Admins and Specialists can view logs.
        """
        params: List[Any] = []
        conditions = ["1=1"]

        # If user is restricted to an organization
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            conditions.append("a.organization_id = ?")
            params.append(user.get("organization_id"))

        if action_filter and action_filter != "All Actions":
            conditions.append("a.action = ?")
            params.append(action_filter)

        if record_type_filter and record_type_filter != "All Types":
            conditions.append("a.record_type = ?")
            params.append(record_type_filter)

        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            conditions.append("(a.business_id LIKE ? OR a.user_email LIKE ? OR a.reason LIKE ?)")
            params.extend([sq, sq, sq])

        params.append(limit)
        where_clause = " AND ".join(conditions)

        sql = f"""
        SELECT a.*, o.name as organization_name
        FROM audit_logs a
        LEFT JOIN organizations o ON a.organization_id = o.id
        WHERE {where_clause}
        ORDER BY a.created_at DESC
        LIMIT ?
        """
        rows = execute_query(sql, tuple(params))
        return [dict(r) for r in rows]
