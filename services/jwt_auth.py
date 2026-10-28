"""
JWT Bearer Authentication and Token Lifecycle Service.
Implements cryptographically signed JSON Web Tokens (HMAC-SHA256, RFC 7519)
for securing headless FastAPI REST endpoints with Role-Based Access Control (RBAC).
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from database.database import execute_query
from services.auth_service import AuthService, PERMISSIONS, hash_password

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "master_data_hub_enterprise_secret_key_2026_qbee_approved")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


class JWTAuthService:
    """Manages token generation, validation, cryptographic verification, and credential checks."""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Encodes claims into a signed JWT bearer token."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": now,
            "iss": "master-data-hub-api"
        })
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """
        Validates token signature and expiration.
        Raises jwt.PyJWTError if invalid or expired.
        """
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], issuer="master-data-hub-api")
        return payload

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies email and password hash against users table."""
        email_clean = email.strip().lower()
        rows = execute_query("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        if not rows:
            return None

        user = dict(rows[0])
        input_hash = hash_password(password)
        if user["password_hash"] != input_hash:
            return None

        # Attach permissions
        user["permissions"] = PERMISSIONS.get(user["role"], {})
        return user
