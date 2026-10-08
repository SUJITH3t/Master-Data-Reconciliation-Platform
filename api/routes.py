"""FastAPI REST Integration Endpoints for Headless Reconciliation Service."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from database.database import init_db
from services.auth_service import AuthService
from services.approval_service import ApprovalService
from services.record_service import RecordService
from services.audit_service import AuditService
from services.validation_service import ValidationService

app = FastAPI(
    title="Master Data Hub REST API",
    description="Enterprise Headless Master Data Ingestion and Reconciliation Service",
    version="1.0.0"
)

# Startup DB init
@app.on_event("startup")
def startup_event():
    init_db()


# Dependency for basic mock auth header in API stubs
def get_current_user(x_user_email: Optional[str] = Header(default="admin@retail.demo")) -> Dict[str, Any]:
    # Default to Admin for headless testing if header not provided
    email = x_user_email or "admin@retail.demo"
    from database.database import execute_query
    rows = execute_query("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid API user credentials")
    user = dict(rows[0])
    from services.auth_service import PERMISSIONS
    user["permissions"] = PERMISSIONS.get(user["role"], {})
    return user


class IngestRecordRequest(BaseModel):
    record_type: str = Field(..., description="Customer, Product, or Supplier")
    organization_id: int = Field(default=1, description="Organization ID")
    source_system: str = Field(..., description="ERP, E-commerce, Store Inventory, or Delivery Partner")
    business_identifier: str = Field(..., description="Entity business key e.g. CUST-001")
    field_values: Dict[str, Any] = Field(..., description="Key-value dictionary of field values")
    verification_status: str = Field(default="Unverified", description="Verified or Unverified")
    source_timestamp: Optional[str] = Field(default=None, description="ISO timestamp")


class RejectRequest(BaseModel):
    reason: str = Field(..., description="Mandatory business reason for rejecting recommendation")


class ApproveRequest(BaseModel):
    notes: Optional[str] = Field(default="Approved via REST API", description="Optional approval notes")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Master Data Hub API"}


@app.post("/api/records/ingest")
def ingest_record(payload: IngestRecordRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Ingest a new raw source record into the staging store."""
    try:
        row_id = RecordService.ingest_source_record(
            record_type=payload.record_type,
            organization_id=payload.organization_id,
            source_system=payload.source_system,
            business_identifier=payload.business_identifier,
            field_values=payload.field_values,
            verification_status=payload.verification_status,
            source_timestamp=payload.source_timestamp
        )
        AuditService.log_event(
            action="API_INGEST_RECORD",
            user=user,
            record_type=payload.record_type,
            business_id=payload.business_identifier,
            decision="INGESTED",
            reason=f"Ingested via API from {payload.source_system}",
            organization_id=payload.organization_id
        )
        return {"success": True, "record_id": row_id, "message": "Source record ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/reconciliation/pending")
def get_pending_reconciliation(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all pending reconciliation cases awaiting review."""
    cases = ApprovalService.get_cases(user=user, status_filter="PENDING")
    return {"count": len(cases), "cases": cases}


@app.get("/api/reconciliation/{record_id}")
def get_reconciliation_details(record_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch reconciliation cases and source evidence for a specific record ID."""
    cases = ApprovalService.get_cases(user=user, search_query=record_id)
    if not cases:
        raise HTTPException(status_code=404, detail=f"No reconciliation cases found for {record_id}")
    return {"record_id": record_id, "cases": cases}


@app.post("/api/reconciliation/{case_id}/approve")
def approve_reconciliation_case(case_id: int, payload: ApproveRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Approve a recommendation."""
    success, msg = ApprovalService.approve_case(case_id, user, notes=payload.notes)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/reconciliation/{case_id}/reject")
def reject_reconciliation_case(case_id: int, payload: RejectRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Reject a recommendation with mandatory reason."""
    success, msg = ApprovalService.reject_case(case_id, user, reason=payload.reason)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/reconciliation/batch")
def run_batch_reconciliation(user: Dict[str, Any] = Depends(get_current_user)):
    """Trigger batch reconciliation across all active source records."""
    summary = ApprovalService.run_reconciliation_batch(user)
    return {"success": True, "summary": summary}


@app.get("/api/audit/{record_id}")
def get_record_audit_log(record_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Get audit trail for a specific master record."""
    logs = AuditService.get_audit_logs(user=user, search_query=record_id)
    return {"record_id": record_id, "audit_events": logs}
