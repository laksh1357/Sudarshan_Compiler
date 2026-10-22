"""
Authentication and Authorization Module for Sudarshan Compiler Studio.
Provides PBKDF2 password hashing, stateless HMAC-SHA256 token issuance and verification,
and FastAPI dependencies for user authentication and role-based access control (RBAC).
"""

import os
import hmac
import json
import base64
import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException, status, Depends
from backend.app.db import get_db

SECRET_KEY = os.getenv("JWT_SECRET", "sudarshan-compiler-studio-secure-key-2026")
TOKEN_EXPIRY_SECONDS = int(os.getenv("TOKEN_EXPIRY_SECONDS", "86400"))  # 24 hours


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Generates a secure random 16-byte salt if not provided.
    """
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return dk.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verifies a plain text password against the stored PBKDF2 hash using constant-time comparison.
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(user_id: int, username: str, role: str, expires_in_seconds: int = TOKEN_EXPIRY_SECONDS) -> str:
    """
    Creates a cryptographically signed stateless session token (HMAC-SHA256).
    Payload includes user id, username, role, and expiration timestamp.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = (now + datetime.timedelta(seconds=expires_in_seconds)).timestamp()

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now.timestamp(),
        "exp": exp
    }

    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = _b64_encode(payload_bytes)

    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies token signature and expiration.
    Returns decoded payload if valid, None otherwise.
    """
    if not token or "." not in token:
        return None

    try:
        payload_b64, signature = token.split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        payload_bytes = _b64_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp", 0)
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        if now > exp:
            return None

        return payload
    except Exception:
        return None


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts authentication token from Authorization header (Bearer <token>)
    or query parameter 'token' or 'auth_token' cookie.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # Query param fallback
    token_query = request.query_params.get("token")
    if token_query:
        return token_query.strip()

    # Cookie fallback
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        return cookie_token.strip()

    return None


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency: authenticates user via token.
    Raises 401 Unauthorized if token is missing or invalid.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account associated with this token no longer exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return dict(row)


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency: attempts to authenticate user, returns None if guest.
    Never raises 401.
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    payload = verify_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    FastAPI dependency: verifies user role is 'admin'.
    Raises 403 Forbidden if user lacks administrative authorization.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required. Access denied."
        )
    return user
