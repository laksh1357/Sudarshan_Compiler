"""
Authentication router: user registration, login, profile inspection, and session logout.
"""

import re
import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field, EmailStr

from backend.app.db import get_db
from backend.app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)
    admin_key: Optional[str] = None  # Optional secret to register as admin directly


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """
    Registers a new user account.
    Validates username format, email format, and password length.
    """
    clean_username = req.username.strip()
    clean_email = req.email.strip().lower()

    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", clean_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username may only contain letters, numbers, underscores, dots, and hyphens."
        )

    if "@" not in clean_email or "." not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # Determine role (if admin_key matches or username is admin)
    role = "user"
    expected_admin_key = "sudarshan-admin-supersecret-2026"
    if req.admin_key and req.admin_key == expected_admin_key:
        role = "admin"

    pwd_hash, salt = hash_password(req.password)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (clean_username, clean_email, pwd_hash, salt, role, now))
            user_id = cursor.lastrowid
    except Exception as e:
        err_msg = str(e).lower()
        if "unique" in err_msg and "username" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{clean_username}' is already registered."
            )
        elif "unique" in err_msg and "email" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{clean_email}' is already registered."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )

    token = create_access_token(user_id=user_id, username=clean_username, role=role)
    user_info = {
        "id": user_id,
        "username": clean_username,
        "email": clean_email,
        "role": role,
        "created_at": now
    }

    return AuthResponse(
        success=True,
        message="Registration successful. Welcome to Sudarshan Compiler Studio!",
        token=token,
        user=user_info
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """
    Authenticates user with username and password.
    Returns signed session token and user profile.
    """
    clean_username = req.username.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password_hash, salt, role, created_at FROM users WHERE username = ? OR email = ?;",
            (clean_username, clean_username.lower())
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    user_dict = dict(row)
    if not verify_password(req.password, user_dict["password_hash"], user_dict["salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    token = create_access_token(user_id=user_dict["id"], username=user_dict["username"], role=user_dict["role"])
    user_info = {
        "id": user_dict["id"],
        "username": user_dict["username"],
        "email": user_dict["email"],
        "role": user_dict["role"],
        "created_at": user_dict["created_at"]
    }

    return AuthResponse(
        success=True,
        message=f"Welcome back, {user_dict['username']}!",
        token=token,
        user=user_info
    )


@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns current authenticated user profile.
    Requires valid session token in Authorization header.
    """
    return {
        "success": True,
        "user": current_user
    }


@router.post("/logout")
def logout():
    """
    Client-side session logout notification.
    Stateless token can be dropped by client.
    """
    return {
        "success": True,
        "message": "Logged out successfully."
    }
