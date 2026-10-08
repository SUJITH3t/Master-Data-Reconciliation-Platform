"""Approval, Rejection, Manual Review, and Publishing Workflow Service."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.database import execute_query, execute_non_query, execute_transaction
from services.auth_service import AuthService
from services.audit_service import AuditService
from services.history_service import HistoryService
from services.record_service import RecordService
from engine.reconciliation import ReconciliationPipeline


class ApprovalService:
    @staticmethod
    def get_cases(
        user: Dict[str, Any],
        status_filter: Optional[str] = None,
        record_type_filter: Optional[str] = None,
        issue_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query reconciliation cases with organization data isolation.
        """
        conditions = ["1=1"]
        params: List[Any] = []

        # Organization isolation
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            conditions.append("rc.organization_id = ?")
            params.append(user.get("organization_id"))

        if status_filter and status_filter != "All Statuses":
            conditions.append("rc.status = ?")
            params.append(status_filter)

        if record_type_filter and record_type_filter != "All Types":
            conditions.append("rc.record_type = ?")
            params.append(record_type_filter)

        if issue_filter and issue_filter != "All Issues":
            conditions.append("rc.issue_type = ?")
            params.append(issue_filter)

        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            conditions.append("(rc.case_number LIKE ? OR rc.business_id LIKE ? OR rc.recommended_value LIKE ?)")
            params.extend([sq, sq, sq])

        params.append(limit)
        where_clause = " AND ".join(conditions)

        sql = f"""
        SELECT rc.*, o.name as organization_name, o.code as organization_code,
               u.full_name as reviewer_name
        FROM reconciliation_cases rc
        JOIN organizations o ON rc.organization_id = o.id
        LEFT JOIN users u ON rc.reviewer_id = u.id
        WHERE {where_clause}
        ORDER BY 
            CASE rc.status
                WHEN 'PENDING' THEN 1
                WHEN 'MANUAL_REVIEW' THEN 2
                WHEN 'APPROVED' THEN 3
                WHEN 'PUBLISHED' THEN 4
                ELSE 5
            END,
            rc.created_at DESC
        LIMIT ?
        """
        rows = execute_query(sql, tuple(params))
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["evidence"] = json.loads(d["evidence_json"]) if d["evidence_json"] else {}
            except Exception:
                d["evidence"] = {}
            results.append(d)
        return results

    @staticmethod
    def get_case_by_id(case_id: int, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch single case with authorization check."""
        sql = """
        SELECT rc.*, o.name as organization_name, o.code as organization_code,
               u.full_name as reviewer_name
        FROM reconciliation_cases rc
        JOIN organizations o ON rc.organization_id = o.id
        LEFT JOIN users u ON rc.reviewer_id = u.id
        WHERE rc.id = ?
        """
        params = [case_id]
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            sql += " AND rc.organization_id = ?"
            params.append(user.get("organization_id"))

        rows = execute_query(sql, tuple(params))
        if not rows:
            return None
        d = dict(rows[0])
        try:
            d["evidence"] = json.loads(d["evidence_json"]) if d["evidence_json"] else {}
        except Exception:
            d["evidence"] = {}
        return d

    @staticmethod
    def approve_case(case_id: int, user: Dict[str, Any], notes: Optional[str] = None) -> Tuple[bool, str]:
        """Approve a reconciliation case."""
        if not AuthService.check_permission(user, "can_approve"):
            return False, "Unauthorized: Your role does not have approval permissions."

        case = ApprovalService.get_case_by_id(case_id, user)
        if not case:
            return False, "Case not found or access denied."

        prev_status = case["status"]
        new_status = "APPROVED"

        # Update case
        sql_update = """
        UPDATE reconciliation_cases
        SET status = ?, reviewer_id = ?, reviewer_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        execute_non_query(sql_update, (new_status, user["id"], notes or "Approved by reviewer", case_id))

        # Record decision
        sql_dec = """
        INSERT INTO reconciliation_decisions (case_id, decision, user_id, reason, previous_status, new_status)
        VALUES (?, 'APPROVE', ?, ?, ?, ?)
        """
        execute_non_query(sql_dec, (case_id, user["id"], notes or "Standard approval", prev_status, new_status))

        # Log audit
        AuditService.log_event(
            action="APPROVE_RECOMMENDATION",
            user=user,
            record_type=case["record_type"],
            business_id=case["business_id"],
            decision="APPROVE",
            reason=notes or f"Approved recommendation for {case['field_name']}: '{case['recommended_value']}'",
            organization_id=case["organization_id"]
        )

        return True, "Recommendation successfully approved. Ready for publishing."

    @staticmethod
    def reject_case(case_id: int, user: Dict[str, Any], reason: str) -> Tuple[bool, str]:
        """Reject a reconciliation recommendation (mandatory reason required)."""
        if not AuthService.check_permission(user, "can_reject"):
            return False, "Unauthorized: Your role does not have rejection permissions."

        if not reason or not reason.strip():
            return False, "A clear business reason is required to reject a recommendation."

        case = ApprovalService.get_case_by_id(case_id, user)
        if not case:
            return False, "Case not found or access denied."

        prev_status = case["status"]
        new_status = "REJECTED"

        sql_update = """
        UPDATE reconciliation_cases
        SET status = ?, reviewer_id = ?, reviewer_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        execute_non_query(sql_update, (new_status, user["id"], reason.strip(), case_id))

        sql_dec = """
        INSERT INTO reconciliation_decisions (case_id, decision, user_id, reason, previous_status, new_status)
        VALUES (?, 'REJECT', ?, ?, ?, ?)
        """
        execute_non_query(sql_dec, (case_id, user["id"], reason.strip(), prev_status, new_status))

        AuditService.log_event(
            action="REJECT_RECOMMENDATION",
            user=user,
            record_type=case["record_type"],
            business_id=case["business_id"],
            decision="REJECT",
            reason=reason.strip(),
            organization_id=case["organization_id"]
        )

        return True, "Recommendation rejected. Status updated to REJECTED."

    @staticmethod
    def request_manual_review(case_id: int, user: Dict[str, Any], reason: str) -> Tuple[bool, str]:
        """Escalate case to MANUAL_REVIEW with reason."""
        if not AuthService.check_permission(user, "can_request_manual_review") and user.get("role") != "Store Manager":
            return False, "Unauthorized: Cannot request manual review."

        case = ApprovalService.get_case_by_id(case_id, user)
        if not case:
            return False, "Case not found or access denied."

        prev_status = case["status"]
        new_status = "MANUAL_REVIEW"

        sql_update = """
        UPDATE reconciliation_cases
        SET status = ?, reviewer_id = ?, reviewer_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        execute_non_query(sql_update, (new_status, user["id"], reason.strip(), case_id))

        sql_dec = """
        INSERT INTO reconciliation_decisions (case_id, decision, user_id, reason, previous_status, new_status)
        VALUES (?, 'MANUAL_REVIEW', ?, ?, ?, ?)
        """
        execute_non_query(sql_dec, (case_id, user["id"], reason.strip(), prev_status, new_status))

        AuditService.log_event(
            action="REQUEST_MANUAL_REVIEW",
            user=user,
            record_type=case["record_type"],
            business_id=case["business_id"],
            decision="MANUAL_REVIEW",
            reason=reason.strip(),
            organization_id=case["organization_id"]
        )

        return True, "Case routed to Human Review queue."

    @staticmethod
    def publish_case(case_id: int, user: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Publish approved recommendation:
        1. Update master table (customers/products/suppliers)
        2. Create change history row
        3. Transition case status to PUBLISHED
        4. Create audit log
        """
        if not AuthService.check_permission(user, "can_publish"):
            return False, "Unauthorized: Your role does not have publishing permissions."

        case = ApprovalService.get_case_by_id(case_id, user)
        if not case:
            return False, "Case not found or access denied."

        if case["status"] not in ("APPROVED", "PENDING"):
            return False, f"Cannot publish case with status '{case['status']}'. Must be APPROVED or PENDING."

        if case["recommended_value"] is None:
            return False, "Cannot publish a null recommendation."

        # 1. Update master table
        RecordService.update_master_field(
            entity_type=case["record_type"],
            business_id=case["business_id"],
            organization_id=case["organization_id"],
            field_name=case["field_name"],
            new_value=case["recommended_value"]
        )

        # 2. Record Change History
        HistoryService.record_change(
            record_type=case["record_type"],
            business_id=case["business_id"],
            organization_id=case["organization_id"],
            field_name=case["field_name"],
            previous_value=case["previous_value"],
            new_value=case["recommended_value"],
            winning_source=case["winning_source"],
            user=user,
            reason=f"Published approved recommendation ({case['case_number']})",
            reconciliation_case_id=case["id"]
        )

        # 3. Update case status to PUBLISHED
        sql_update = """
        UPDATE reconciliation_cases
        SET status = 'PUBLISHED', resolved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        execute_non_query(sql_update, (case_id,))

        # 4. Record Decision
        sql_dec = """
        INSERT INTO reconciliation_decisions (case_id, decision, user_id, reason, previous_status, new_status)
        VALUES (?, 'PUBLISH', ?, 'Published to master dataset', ?, 'PUBLISHED')
        """
        execute_non_query(sql_dec, (case_id, user["id"], case["status"]))

        # 5. Audit Log
        AuditService.log_event(
            action="PUBLISH_MASTER_DATA",
            user=user,
            record_type=case["record_type"],
            business_id=case["business_id"],
            decision="PUBLISHED",
            reason=f"Master record field {case['field_name']} updated to '{case['recommended_value']}' from {case['winning_source']}",
            organization_id=case["organization_id"]
        )

        return True, f"Master {case['record_type']} record {case['business_id']} successfully updated and published."

    @staticmethod
    def run_reconciliation_batch(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run reconciliation engine across all ingested source records for user's organization.
        Processes entities, detects conflicts, creates or updates reconciliation cases.
        """
        pipeline = ReconciliationPipeline()

        # Fetch distinct entities from source_records
        sql = """
        SELECT DISTINCT record_type, business_identifier, organization_id
        FROM source_records
        """
        params = []
        if user.get("role") not in ("Admin", "Reconciliation Specialist"):
            sql += " WHERE organization_id = ?"
            params.append(user.get("organization_id"))

        entity_rows = execute_query(sql, tuple(params))

        total_processed = 0
        resolved_auto = 0
        manual_review = 0
        failed_count = 0

        # Define candidate fields per entity type
        entity_fields = {
            "Customer": ["email", "phone", "address"],
            "Product": ["price", "status", "sku"],
            "Supplier": ["email", "phone", "status"]
        }

        for ent in entity_rows:
            rec_type = ent["record_type"]
            bus_id = ent["business_identifier"]
            org_id = ent["organization_id"]

            fields_to_check = entity_fields.get(rec_type, [])

            # Get all source records for this entity
            src_records = RecordService.get_source_records_for_entity(rec_type, bus_id, user)
            if not src_records:
                continue

            master_rec = RecordService.get_single_master_record(rec_type, bus_id, user)

            for f_name in fields_to_check:
                total_processed += 1
                curr_val = master_rec.get(f_name) if master_rec else None

                recon_res = pipeline.process_entity_field(
                    entity_type=rec_type,
                    business_id=bus_id,
                    field_name=f_name,
                    source_records=src_records,
                    current_master_value=curr_val
                )

                # If unanimous and matches master value, no case needed unless empty
                if recon_res["issue_type"] == "None" and str(recon_res["recommended_value"]) == str(curr_val):
                    resolved_auto += 1
                    continue

                case_num = f"REC-{rec_type[:3].upper()}-{bus_id}-{f_name.upper()}"
                status = recon_res["status"]

                if status == "MANUAL_REVIEW":
                    manual_review += 1
                elif status == "PENDING":
                    resolved_auto += 1
                else:
                    failed_count += 1

                # Upsert into reconciliation_cases
                sql_upsert = """
                INSERT INTO reconciliation_cases (
                    case_number, record_type, business_id, organization_id,
                    field_name, issue_type, recommended_value, winning_source,
                    previous_value, confidence_score, status, reason, explanation,
                    evidence_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(case_number) DO UPDATE SET
                    issue_type = excluded.issue_type,
                    recommended_value = excluded.recommended_value,
                    winning_source = excluded.winning_source,
                    previous_value = excluded.previous_value,
                    confidence_score = excluded.confidence_score,
                    reason = excluded.reason,
                    explanation = excluded.explanation,
                    evidence_json = excluded.evidence_json,
                    updated_at = CURRENT_TIMESTAMP
                """
                execute_non_query(
                    sql_upsert,
                    (
                        case_num, rec_type, bus_id, org_id,
                        f_name, recon_res["issue_type"],
                        str(recon_res["recommended_value"]) if recon_res["recommended_value"] is not None else None,
                        recon_res["winning_source"],
                        str(curr_val) if curr_val is not None else None,
                        recon_res["confidence"],
                        status,
                        recon_res["reason"],
                        recon_res["explanation"],
                        json.dumps(recon_res["evidence"])
                    )
                )

        AuditService.log_event(
            action="RUN_BATCH_RECONCILIATION",
            user=user,
            record_type="ALL",
            decision="EXECUTE",
            reason=f"Processed {total_processed} field reconciliations: {resolved_auto} automatic candidates, {manual_review} manual review, {failed_count} unresolved."
        )

        return {
            "records_processed": total_processed,
            "resolved_automatically": resolved_auto,
            "manual_review": manual_review,
            "failed": failed_count
        }
