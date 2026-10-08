"""Test Role-Based Access Control and Organization Data Isolation."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.seed import seed_database
from database.database import execute_query
from services.auth_service import AuthService
from services.record_service import RecordService
from services.approval_service import ApprovalService


def setup_module():
    seed_database(force=False)


def test_rbac_permission_matrix():
    admin = AuthService.authenticate("admin@retail.demo", "Admin123!")
    specialist = AuthService.authenticate("specialist@retail.demo", "Spec123!")
    manager = AuthService.authenticate("manager@retail.demo", "Store123!")
    partner = AuthService.authenticate("partner@delivery.demo", "Partner123!")

    assert admin is not None and admin["role"] == "Admin"
    assert specialist is not None and specialist["role"] == "Reconciliation Specialist"
    assert manager is not None and manager["role"] == "Store Manager"
    assert partner is not None and partner["role"] == "External Partner"

    # Rule editing permission
    assert AuthService.check_permission(admin, "can_edit_rules") is True
    assert AuthService.check_permission(manager, "can_edit_rules") is False
    assert AuthService.check_permission(partner, "can_edit_rules") is False

    # Approval permission
    assert AuthService.check_permission(admin, "can_approve") is True
    assert AuthService.check_permission(specialist, "can_approve") is True
    assert AuthService.check_permission(partner, "can_approve") is False


def test_organization_data_isolation():
    """External Partner can ONLY see Delivery Partner records (Organization ID 3)."""
    admin = AuthService.authenticate("admin@retail.demo", "Admin123!")
    partner = AuthService.authenticate("partner@delivery.demo", "Partner123!")

    # Admin sees all suppliers
    admin_suppliers = RecordService.get_master_records("Supplier", admin)
    assert len(admin_suppliers) >= 15

    # Partner only sees suppliers assigned to Delivery Partner org
    partner_suppliers = RecordService.get_master_records("Supplier", partner)
    assert len(partner_suppliers) > 0
    for s in partner_suppliers:
        assert s["organization_id"] == partner["organization_id"]


def test_unauthorized_operation_blocked():
    partner = AuthService.authenticate("partner@delivery.demo", "Partner123!")
    cases = ApprovalService.get_cases(partner)
    if cases:
        case_id = cases[0]["id"]
        success, msg = ApprovalService.approve_case(case_id, partner)
        assert success is False
        assert "Unauthorized" in msg


def test_approval_and_publishing_persistence():
    """
    Test End-to-End Approval & Publishing workflow (Section 68):
    Pending -> Approve -> Approved -> Publish -> Master record updated -> Change history created -> Audit log created.
    """
    admin = AuthService.authenticate("admin@retail.demo", "Admin123!")
    cases = ApprovalService.get_cases(admin, status_filter="PENDING")
    assert len(cases) > 0, "Expected at least one pending case"
    case = cases[0]
    case_id = case["id"]

    # 1. Approve
    ok_app, msg_app = ApprovalService.approve_case(case_id, admin, notes="Automated test approval")
    assert ok_app is True

    case_after_app = ApprovalService.get_case_by_id(case_id, admin)
    assert case_after_app["status"] == "APPROVED"

    # 2. Publish
    ok_pub, msg_pub = ApprovalService.publish_case(case_id, admin)
    assert ok_pub is True

    case_after_pub = ApprovalService.get_case_by_id(case_id, admin)
    assert case_after_pub["status"] == "PUBLISHED"

    # 3. Verify Master record was updated
    master_rec = RecordService.get_single_master_record(case["record_type"], case["business_id"], admin)
    assert master_rec is not None
    assert str(master_rec[case["field_name"]]) == str(case["recommended_value"])

    # 4. Verify Change History was created
    from services.history_service import HistoryService
    hist = HistoryService.get_change_history(admin, record_type=case["record_type"], business_id=case["business_id"])
    assert len(hist) > 0
    assert hist[0]["reconciliation_case_id"] == case_id

    # 5. Verify Audit Log was created
    from services.audit_service import AuditService
    audits = AuditService.get_audit_logs(admin, search_query=case["business_id"])
    assert any(a["action"] == "PUBLISH_MASTER_DATA" for a in audits)
