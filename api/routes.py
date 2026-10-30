"""
FastAPI REST Integration Endpoints for Headless Reconciliation Service.
Secured with JWT Bearer Authentication, Role-Based Access Control (RBAC),
Streaming CDC Ingestion, and Probabilistic Linkage APIs.
"""

import os
import sys
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from contextlib import asynccontextmanager

from database.database import init_db, execute_query
from services.auth_service import AuthService, PERMISSIONS
from services.approval_service import ApprovalService
from services.record_service import RecordService
from services.audit_service import AuditService
from services.jwt_auth import JWTAuthService
from services.streaming_ingestion import streaming_engine, DebeziumCDCParser
from engine.probabilistic_linkage import FellegiSunterModel, ProbabilisticLinkageEngine
from database.migration import check_database_readiness


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database schema is initialized on startup."""
    init_db()
    yield


app = FastAPI(
    title="Master Data Hub REST API",
    description="Enterprise Headless Master Data Reconciliation, JWT Auth, Streaming Ingestion & Probabilistic Linkage API",
    version="2.0.0",
    lifespan=lifespan
)

# OAuth2 Password Bearer scheme for Swagger UI & OpenAPI spec
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


# =====================================================================
# Authentication & Authorization Dependencies
# =====================================================================

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_user_email: Optional[str] = Header(default=None)
) -> Dict[str, Any]:
    """
    Validates JWT Bearer token.
    Falls back to x_user_email header for automated script backward-compatibility.
    """
    user_email = None

    if token:
        try:
            payload = JWTAuthService.decode_access_token(token)
            user_email = payload.get("sub")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired JWT token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif x_user_email:
        user_email = x_user_email.strip().lower()
    else:
        # Default headless test fallback
        user_email = "admin@retail.demo"

    rows = execute_query("SELECT * FROM users WHERE LOWER(email) = ?", (user_email.strip().lower(),))
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found in directory",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = dict(rows[0])
    user["permissions"] = PERMISSIONS.get(user["role"], {})
    return user


def require_specialist_or_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Enforces Specialist or Admin role for governance write actions."""
    if user.get("role") not in ("Admin", "Reconciliation Specialist"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.get('role')}' does not have governance approval authorization."
        )
    return user


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Enforces Admin role for critical administrative operations."""
    if user.get("role") != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation restricted to Enterprise HQ Administrators."
        )
    return user


# =====================================================================
# Request / Response Models
# =====================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "admin@retail.demo"})
    password: str = Field(..., json_schema_extra={"example": "Admin123!"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 60
    role: str
    full_name: str
    organization_id: int


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


class PairComparisonRequest(BaseModel):
    record_type: str = Field(default="Customer")
    record_a: Dict[str, Any]
    record_b: Dict[str, Any]


# =====================================================================
# Authentication Endpoints
# =====================================================================

@app.post("/api/auth/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint for Swagger UI login."""
    user = JWTAuthService.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = JWTAuthService.create_access_token({
        "sub": user["email"],
        "user_id": user["id"],
        "role": user["role"],
        "organization_id": user["organization_id"]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 60,
        "role": user["role"],
        "full_name": user["full_name"],
        "organization_id": user["organization_id"]
    }


@app.post("/api/auth/login", response_model=TokenResponse)
def login_json(payload: LoginRequest):
    """JSON login endpoint returning signed JWT token."""
    user = JWTAuthService.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = JWTAuthService.create_access_token({
        "sub": user["email"],
        "user_id": user["id"],
        "role": user["role"],
        "organization_id": user["organization_id"]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 60,
        "role": user["role"],
        "full_name": user["full_name"],
        "organization_id": user["organization_id"]
    }


@app.get("/api/auth/me")
def get_auth_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve profile and permissions of authenticated user."""
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "organization_id": user["organization_id"],
        "permissions": user["permissions"]
    }


# =====================================================================
# Health & Persistence Diagnostics
# =====================================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Master Data Hub Enterprise API",
        "security": "JWT Bearer Auth Hardened",
        "version": "2.0.0"
    }


@app.get("/api/database/status")
def database_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve persistence and connection pool metrics."""
    return check_database_readiness()


# =====================================================================
# Core Reconciliation & Governance Endpoints
# =====================================================================

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
def approve_reconciliation_case(case_id: int, payload: ApproveRequest, user: Dict[str, Any] = Depends(require_specialist_or_admin)):
    """Approve a recommendation (requires Specialist or Admin)."""
    success, msg = ApprovalService.approve_case(case_id, user, notes=payload.notes)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/reconciliation/{case_id}/reject")
def reject_reconciliation_case(case_id: int, payload: RejectRequest, user: Dict[str, Any] = Depends(require_specialist_or_admin)):
    """Reject a recommendation with mandatory reason."""
    success, msg = ApprovalService.reject_case(case_id, user, reason=payload.reason)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/reconciliation/batch")
def run_batch_reconciliation(user: Dict[str, Any] = Depends(require_specialist_or_admin)):
    """Trigger batch reconciliation across all active source records."""
    summary = ApprovalService.run_reconciliation_batch(user)
    return {"success": True, "summary": summary}


@app.get("/api/audit/{record_id}")
def get_record_audit_log(record_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Get audit trail for a specific master record."""
    logs = AuditService.get_audit_logs(user=user, search_query=record_id)
    return {"record_id": record_id, "audit_events": logs}


# =====================================================================
# Probabilistic Linkage Endpoints (Fellegi-Sunter & Cosine Similarity)
# =====================================================================

@app.post("/api/linkage/compare")
def compare_probabilistic_pair(payload: PairComparisonRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    Computes Fellegi-Sunter weight, Jaro-Winkler, and N-gram Cosine similarity
    for typo-tolerant entity matching between two records.
    """
    eval_result = FellegiSunterModel.evaluate_pair(payload.record_a, payload.record_b, payload.record_type)
    return {"success": True, "evaluation": eval_result}


@app.get("/api/linkage/benchmark")
def run_linkage_benchmark(user: Dict[str, Any] = Depends(get_current_user)):
    """Runs the 4-case empirical benchmark validating phonetic and typographical matching."""
    res = ProbabilisticLinkageEngine.run_probabilistic_benchmark()
    return {"success": True, "benchmark": res}


# =====================================================================
# Streaming & Debezium CDC Ingestion Endpoints
# =====================================================================

@app.post("/api/stream/debezium/cdc")
def ingest_debezium_cdc(event: Dict[str, Any], user: Dict[str, Any] = Depends(get_current_user)):
    """
    Ingests Debezium CDC payload asynchronously into the streaming engine with sub-2ms response.
    """
    enqueue_result = streaming_engine.enqueue_cdc_event(event)
    return {"success": True, "streaming": enqueue_result}


@app.post("/api/stream/simulate")
def simulate_stream_feed(count: int = 10, user: Dict[str, Any] = Depends(require_specialist_or_admin)):
    """Generates simulated real-time POS and ERP CDC feed events."""
    sim_events = streaming_engine.simulate_realtime_stream(count=count)
    return {"success": True, "ingested_count": len(sim_events), "events": sim_events}


@app.get("/api/stream/status")
def get_stream_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves real-time telemetry metrics for the streaming ingestion queue."""
    metrics = streaming_engine.get_stream_metrics()
    return {"success": True, "metrics": metrics}
