"""
Administrative router: Role-Based Access Control (RBAC) demonstration.
Only accounts with 'admin' role are authorized to access these endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from backend.app.db import get_db, get_db_health
from backend.app.auth import require_admin

router = APIRouter(prefix="/admin", tags=["Administrative (RBAC)"])


@router.get("/stats")
def get_admin_stats(admin_user: dict = Depends(require_admin)):
    """
    Returns administrative overview of platform metrics and database health.
    Strictly restricted to users with role = 'admin'.
    """
    db_info = get_db_health()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role;")
        role_counts = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("SELECT language, COUNT(*) FROM snippets GROUP BY language;")
        lang_counts = {r[0]: r[1] for r in cursor.fetchall()}

    return {
        "success": True,
        "operator": admin_user["username"],
        "authorization": "Granted (admin role verified)",
        "users_by_role": role_counts,
        "snippets_by_language": lang_counts,
        "database": db_info
    }


@router.get("/users")
def list_all_users(admin_user: dict = Depends(require_admin)):
    """
    Lists all registered accounts in the system.
    Restricted to administrative users.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY id ASC;")
        users = [dict(r) for r in cursor.fetchall()]

    return {
        "success": True,
        "count": len(users),
        "users": users
    }


@router.get("/snippets")
def list_all_snippets(admin_user: dict = Depends(require_admin)):
    """
    Lists all snippets across all users for moderation and audit.
    Restricted to administrative users.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.user_id, u.username as author, s.title, s.description,
                   s.language, s.is_public, s.created_at, s.updated_at
            FROM snippets s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.id DESC;
        """)
        snippets = [dict(r) for r in cursor.fetchall()]

    for s in snippets:
        s["is_public"] = bool(s["is_public"])

    return {
        "success": True,
        "count": len(snippets),
        "snippets": snippets
    }


@router.delete("/snippets/{snippet_id}")
def admin_delete_snippet(snippet_id: int, admin_user: dict = Depends(require_admin)):
    """
    Allows administrator to delete any snippet (moderation action).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, user_id FROM snippets WHERE id = ?;", (snippet_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snippet with ID {snippet_id} not found."
            )

        cursor.execute("DELETE FROM snippets WHERE id = ?;", (snippet_id,))

    return {
        "success": True,
        "message": f"Administrative removal: Snippet '{row['title']}' was deleted by admin {admin_user['username']}."
    }
