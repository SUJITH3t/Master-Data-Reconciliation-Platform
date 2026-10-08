"""Authentication and Role-Based Access Control (RBAC) Service."""

import hashlib
from typing import Any, Dict, List, Optional
from database.database import execute_query


def hash_password(password: str) -> str:
    """Deterministic hash for demo accounts."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Permissions definition matrix
PERMISSIONS = {
    "Store Manager": {
        "view_store_records": True,
        "view_all_orgs": False,
        "view_conflicts": True,
        "view_recommendations": True,
        "can_approve": True,
        "can_reject": True,
        "can_publish": True,
        "can_edit_rules": False,
        "can_view_admin": False,
        "can_modify_audit": False,
        "can_view_audit": False,
        "can_run_validation": True,
    },
    "Reconciliation Specialist": {
        "view_store_records": True,
        "view_all_orgs": True,
        "view_conflicts": True,
        "view_recommendations": True,
        "can_approve": True,
        "can_reject": True,
        "can_publish": True,
        "can_request_manual_review": True,
        "can_edit_rules": False,
        "can_view_admin": False,
        "can_modify_audit": False,
        "can_view_audit": True,
        "can_run_validation": True,
    },
    "Admin": {
        "view_store_records": True,
        "view_all_orgs": True,
        "view_conflicts": True,
        "view_recommendations": True,
        "can_approve": True,
        "can_reject": True,
        "can_publish": True,
        "can_request_manual_review": True,
        "can_edit_rules": True,
        "can_view_admin": True,
        "can_modify_audit": False, # Nobody can modify audit log
        "can_view_audit": True,
        "can_run_validation": True,
    },
    "External Partner": {
        "view_store_records": False,
        "view_all_orgs": False,
        "view_conflicts": True,
        "view_recommendations": True,
        "can_approve": False,
        "can_reject": False,
        "can_publish": False,
        "can_request_manual_review": False,
        "can_edit_rules": False,
        "can_view_admin": False,
        "can_modify_audit": False,
        "can_view_audit": False,
        "can_run_validation": False,
    }
}


class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email and password hash."""
        pwd_hash = hash_password(password)
        rows = execute_query(
            """
            SELECT u.id, u.email, u.full_name, u.role, u.organization_id, u.is_active,
                   o.name as organization_name, o.code as organization_code
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = ? AND u.password_hash = ? AND u.is_active = 1
            """,
            (email.strip().lower(), pwd_hash)
        )
        if rows:
            user = dict(rows[0])
            user["permissions"] = PERMISSIONS.get(user["role"], {})
            return user
        return None

    @staticmethod
    def get_demo_users() -> List[Dict[str, Any]]:
        """Fetch pre-configured demo users for testing."""
        rows = execute_query(
            """
            SELECT u.id, u.email, u.full_name, u.role, u.organization_id,
                   o.name as organization_name, o.code as organization_code
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            ORDER BY u.id ASC
            """
        )
        return [dict(r) for r in rows]

    @staticmethod
    def check_permission(user: Optional[Dict[str, Any]], permission: str) -> bool:
        """Enforce strict permission check."""
        if not user:
            return False
        role = user.get("role", "")
        return PERMISSIONS.get(role, {}).get(permission, False)

    @staticmethod
    def verify_org_access(user: Dict[str, Any], target_org_id: int) -> bool:
        """
        Check if user is authorized to access records belonging to target_org_id.
        Admins can access all. Others can only access their assigned organization.
        """
        if not user:
            return False
        if user.get("role") in ("Admin", "Reconciliation Specialist"):
            return True
        return user.get("organization_id") == target_org_id
