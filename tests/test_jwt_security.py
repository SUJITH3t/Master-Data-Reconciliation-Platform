"""
Unit and Integration Tests for JWT Bearer Authentication and FastAPI Security Hardening.
"""

import pytest
import jwt
from datetime import timedelta
from fastapi.testclient import TestClient

from api.routes import app
from services.jwt_auth import JWTAuthService, JWT_SECRET_KEY, JWT_ALGORITHM

client = TestClient(app)


def test_jwt_token_creation_and_decoding():
    """Verify signed JWT token creation and payload extraction."""
    payload = {
        "sub": "admin@retail.demo",
        "user_id": 1,
        "role": "Admin",
        "organization_id": 1
    }
    token = JWTAuthService.create_access_token(payload)
    decoded = JWTAuthService.decode_access_token(token)

    assert decoded["sub"] == "admin@retail.demo"
    assert decoded["role"] == "Admin"
    assert decoded["iss"] == "master-data-hub-api"
    assert "exp" in decoded


def test_jwt_invalid_signature_rejection():
    """Verify that tokens signed with a different key are rejected."""
    tampered_token = jwt.encode(
        {"sub": "attacker@fake.com", "role": "Admin"},
        "wrong_secret_key_1234567890_32bytes_pad",
        algorithm="HS256"
    )
    with pytest.raises(jwt.PyJWTError):
        JWTAuthService.decode_access_token(tampered_token)


def test_jwt_expired_token_rejection():
    """Verify expired JWT tokens are rejected."""
    expired_token = JWTAuthService.create_access_token(
        {"sub": "admin@retail.demo", "role": "Admin"},
        expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        JWTAuthService.decode_access_token(expired_token)


def test_api_login_endpoint():
    """Verify /api/auth/login generates valid JWT bearer token."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@retail.demo", "password": "Admin123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Admin"


def test_api_protected_route_with_jwt():
    """Verify protected route allows access with valid Bearer token."""
    # 1. Login to get token
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "admin@retail.demo", "password": "Admin123!"}
    )
    token = login_resp.json()["access_token"]

    # 2. Access /api/auth/me
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    user_data = resp.json()
    assert user_data["email"] == "admin@retail.demo"
    assert user_data["role"] == "Admin"
    assert user_data["permissions"]["can_approve"] is True


def test_api_rbac_forbidden_for_external_partner():
    """Verify External Partner role is blocked from approving cases."""
    # Login as external partner
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "partner@delivery.demo", "password": "Partner123!"}
    )
    assert login_resp.status_code == 200
    partner_token = login_resp.json()["access_token"]

    # Attempt to call approve endpoint
    resp = client.post(
        "/api/reconciliation/1/approve",
        json={"notes": "Malicious attempt"},
        headers={"Authorization": f"Bearer {partner_token}"}
    )
    assert resp.status_code == 403
