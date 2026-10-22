"""
Comprehensive Test Suite for Database Connectivity, Authentication, and Authorization (RBAC).
Tests Checks 5, 6, and 7 of the Sudarshan Compiler Studio deployment checklist.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.main import app
from backend.app.db import get_db, init_db, get_db_health
from backend.app.auth import hash_password, verify_password, create_access_token, verify_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()


# ==============================================================================
# CHECK 5: DATABASE CONNECTIVITY & CRUD OPERATIONS
# ==============================================================================

def test_database_connectivity_and_health():
    """Verify database connection, schema tables, and health status."""
    health = get_db_health()
    assert health["status"] == "connected"
    assert health["dialect"] == "sqlite3"
    assert "users" in health["tables"]
    assert "snippets" in health["tables"]
    assert "compilation_history" in health["tables"]
    assert health["tables"]["users"] >= 2  # seeded admin and developer accounts


def test_database_health_endpoint():
    """Verify GET /api/db/health endpoint returns 200 with schema metadata."""
    resp = client.get("/api/db/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "connected"
    assert data["dialect"] == "sqlite3"


def test_database_transaction_commit_and_rollback():
    """Verify transaction atomicity and rollback behavior on exception."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM snippets;")
        initial_count = cursor.fetchone()[0]

    # Test rollback on exception
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snippets (user_id, title, description, language, code, is_public, created_at, updated_at)
                VALUES (1, 'Rollback Test', '', 'sudarshan', 'print(1);', 0, '2026-01-01', '2026-01-01');
            """)
            raise RuntimeError("Intentional error triggering transaction rollback")
    except RuntimeError:
        pass

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM snippets;")
        after_count = cursor.fetchone()[0]
        assert after_count == initial_count  # No row leaked


# ==============================================================================
# CHECK 6: AUTHENTICATION (SIGNUP, LOGIN, TOKENS, LOGOUT, ME)
# ==============================================================================

def test_password_hashing_and_verification():
    """Verify PBKDF2-HMAC-SHA256 password hashing with salt and constant-time check."""
    pwd = "SecurePassword@2026"
    h, salt = hash_password(pwd)
    assert len(h) == 64
    assert len(salt) == 32
    assert verify_password(pwd, h, salt) is True
    assert verify_password("WrongPassword", h, salt) is False


def test_stateless_access_token_creation_and_verification():
    """Verify HMAC-SHA256 token issuance and expiration validation."""
    token = create_access_token(user_id=42, username="alice", role="user", expires_in_seconds=3600)
    payload = verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == 42
    assert payload["username"] == "alice"
    assert payload["role"] == "user"

    # Expired token test
    expired_token = create_access_token(user_id=42, username="alice", role="user", expires_in_seconds=-10)
    assert verify_access_token(expired_token) is None

    # Tampered token test
    tampered = token[:-4] + "abcd"
    assert verify_access_token(tampered) is None


def test_user_registration_success():
    """Verify new user signup returns token and HTTP 201."""
    import uuid
    uname = f"testuser_{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/auth/register", json={
        "username": uname,
        "email": f"{uname}@example.com",
        "password": "Password123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["token"] is not None
    assert data["user"]["username"] == uname
    assert data["user"]["role"] == "user"


def test_user_registration_duplicate_rejection():
    """Verify duplicate username returns HTTP 409 Conflict."""
    resp = client.post("/api/auth/register", json={
        "username": "developer",  # already seeded
        "email": "another_dev@example.com",
        "password": "Password123"
    })
    assert resp.status_code == 409


def test_user_login_success():
    """Verify seeded developer login with valid credentials."""
    resp = client.post("/api/auth/login", json={
        "username": "developer",
        "password": "Dev@123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["token"] is not None
    assert data["user"]["username"] == "developer"
    assert data["user"]["role"] == "user"


def test_user_login_invalid_password():
    """Verify login failure with incorrect password returns HTTP 401."""
    resp = client.post("/api/auth/login", json={
        "username": "developer",
        "password": "WrongPassword999"
    })
    assert resp.status_code == 401


def test_profile_me_authenticated():
    """Verify GET /api/auth/me returns profile when valid Bearer token provided."""
    login_resp = client.post("/api/auth/login", json={
        "username": "developer",
        "password": "Dev@123"
    })
    token = login_resp.json()["token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["user"]["username"] == "developer"


def test_profile_me_unauthenticated():
    """Verify GET /api/auth/me returns HTTP 401 when no token is supplied."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_endpoint():
    """Verify POST /api/auth/logout endpoint."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ==============================================================================
# CHECK 7: AUTHORIZATION & ROLE-BASED ACCESS CONTROL (RBAC)
# ==============================================================================

def test_admin_access_allowed():
    """Verify administrator can access restricted admin dashboard endpoints."""
    login_resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "Admin@123"
    })
    admin_token = login_resp.json()["token"]

    # 1. Admin stats
    resp_stats = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_stats.status_code == 200
    data_stats = resp_stats.json()
    assert data_stats["success"] is True
    assert data_stats["operator"] == "admin"
    assert "users_by_role" in data_stats

    # 2. Admin users list
    resp_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_users.status_code == 200
    assert resp_users.json()["count"] >= 2

    # 3. Admin snippets list
    resp_snippets = client.get("/api/admin/snippets", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_snippets.status_code == 200
    assert resp_snippets.json()["count"] >= 1


def test_non_admin_forbidden_from_admin_endpoints():
    """Verify standard user (role='user') is rejected with HTTP 403 Forbidden on admin endpoints."""
    login_resp = client.post("/api/auth/login", json={
        "username": "developer",
        "password": "Dev@123"
    })
    user_token = login_resp.json()["token"]

    # Developer attempting to access /api/admin/stats
    resp_stats = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert resp_stats.status_code == 403

    # Developer attempting to access /api/admin/users
    resp_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp_users.status_code == 403


# ==============================================================================
# DATABASE CRUD ON CODE SNIPPETS WITH AUTH & AUTHORIZATION
# ==============================================================================

def test_snippet_crud_lifecycle_and_ownership():
    """Verify create, read, update, and delete on code snippets with authorization checks."""
    login_resp = client.post("/api/auth/login", json={
        "username": "developer",
        "password": "Dev@123"
    })
    dev_token = login_resp.json()["token"]

    # 1. CREATE snippet
    create_resp = client.post(
        "/api/snippets",
        json={
            "title": "My Test Loop",
            "description": "Custom loop in Sudarshan",
            "language": "sudarshan",
            "code": "int i = 0;\nwhile (i < 5) {\n  print(i);\n  i = i + 1;\n}",
            "is_public": False
        },
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert create_resp.status_code == 201
    snippet_id = create_resp.json()["snippet_id"]

    # 2. READ my snippets
    list_resp = client.get("/api/snippets", headers={"Authorization": f"Bearer {dev_token}"})
    assert list_resp.status_code == 200
    my_snippets = list_resp.json()["snippets"]
    assert any(s["id"] == snippet_id for s in my_snippets)

    # 3. UPDATE snippet
    update_resp = client.put(
        f"/api/snippets/{snippet_id}",
        json={"title": "Updated Test Loop Title"},
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert update_resp.status_code == 200

    # 4. GET by ID
    get_resp = client.get(f"/api/snippets/{snippet_id}", headers={"Authorization": f"Bearer {dev_token}"})
    assert get_resp.status_code == 200
    assert get_resp.json()["snippet"]["title"] == "Updated Test Loop Title"

    # 5. Non-owner / unauthorized user cannot view private snippet
    anon_resp = client.get(f"/api/snippets/{snippet_id}")
    assert anon_resp.status_code == 403

    # 6. DELETE snippet
    del_resp = client.delete(f"/api/snippets/{snippet_id}", headers={"Authorization": f"Bearer {dev_token}"})
    assert del_resp.status_code == 200

    # Verify deleted
    get_after_del = client.get(f"/api/snippets/{snippet_id}", headers={"Authorization": f"Bearer {dev_token}"})
    assert get_after_del.status_code == 404


def test_public_snippets_accessible_anonymously():
    """Verify GET /api/snippets/public is accessible without any authentication."""
    resp = client.get("/api/snippets/public")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["snippets"], list)
