"""
Snippets router: CRUD operations on saved code snippets.
Demonstrates database connectivity, transactions, foreign key constraints, and authorization.
"""

import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.app.db import get_db
from backend.app.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/snippets", tags=["Code Snippets"])


class SnippetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)
    language: str = Field("sudarshan", min_length=1, max_length=32)
    code: str = Field(..., min_length=1)
    is_public: bool = False


class SnippetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, min_length=1, max_length=32)
    code: Optional[str] = Field(None, min_length=1)
    is_public: Optional[bool] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_snippet(snippet: SnippetCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new saved code snippet for the authenticated user.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO snippets (user_id, title, description, language, code, is_public, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            current_user["id"],
            snippet.title.strip(),
            (snippet.description or "").strip(),
            snippet.language.strip().lower(),
            snippet.code,
            1 if snippet.is_public else 0,
            now,
            now
        ))
        snippet_id = cursor.lastrowid

    return {
        "success": True,
        "message": f"Snippet '{snippet.title}' saved successfully.",
        "snippet_id": snippet_id
    }


@router.get("")
def list_my_snippets(current_user: dict = Depends(get_current_user)):
    """
    Lists all snippets belonging to the currently authenticated user.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, language, code, is_public, created_at, updated_at
            FROM snippets
            WHERE user_id = ?
            ORDER BY updated_at DESC;
        """, (current_user["id"],))
        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        r["is_public"] = bool(r["is_public"])

    return {
        "success": True,
        "count": len(rows),
        "snippets": rows
    }


@router.get("/public")
def list_public_snippets():
    """
    Lists all public snippets available to the community (no auth required).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.description, s.language, s.code, s.created_at, s.updated_at,
                   u.username as author
            FROM snippets s
            JOIN users u ON s.user_id = u.id
            WHERE s.is_public = 1
            ORDER BY s.updated_at DESC
            LIMIT 50;
        """)
        rows = [dict(r) for r in cursor.fetchall()]

    return {
        "success": True,
        "count": len(rows),
        "snippets": rows
    }


@router.get("/{snippet_id}")
def get_snippet(snippet_id: int, current_user: Optional[dict] = Depends(get_optional_user)):
    """
    Retrieves a single snippet by ID.
    Authorized if snippet is public, or if caller is author or administrator.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.user_id, s.title, s.description, s.language, s.code, s.is_public,
                   s.created_at, s.updated_at, u.username as author
            FROM snippets s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = ?;
        """, (snippet_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snippet with ID {snippet_id} not found."
        )

    snippet_dict = dict(row)
    snippet_dict["is_public"] = bool(snippet_dict["is_public"])

    # Authorization check
    is_owner = current_user and current_user.get("id") == snippet_dict["user_id"]
    is_admin = current_user and current_user.get("role") == "admin"

    if not snippet_dict["is_public"] and not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this private snippet."
        )

    return {
        "success": True,
        "snippet": snippet_dict
    }


@router.put("/{snippet_id}")
def update_snippet(snippet_id: int, update_data: SnippetUpdate, current_user: dict = Depends(get_current_user)):
    """
    Updates an existing snippet.
    Only the snippet owner or an administrator is authorized.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, title FROM snippets WHERE id = ?;", (snippet_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snippet with ID {snippet_id} not found."
            )

        # Authorization check: owner or admin
        if row["user_id"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have authorization to edit this snippet."
            )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fields = []
        values = []

        if update_data.title is not None:
            fields.append("title = ?")
            values.append(update_data.title.strip())
        if update_data.description is not None:
            fields.append("description = ?")
            values.append(update_data.description.strip())
        if update_data.language is not None:
            fields.append("language = ?")
            values.append(update_data.language.strip().lower())
        if update_data.code is not None:
            fields.append("code = ?")
            values.append(update_data.code)
        if update_data.is_public is not None:
            fields.append("is_public = ?")
            values.append(1 if update_data.is_public else 0)

        if not fields:
            return {"success": True, "message": "No changes requested."}

        fields.append("updated_at = ?")
        values.append(now)
        values.append(snippet_id)

        sql = f"UPDATE snippets SET {', '.join(fields)} WHERE id = ?;"
        cursor.execute(sql, tuple(values))

    return {
        "success": True,
        "message": f"Snippet {snippet_id} updated successfully."
    }


@router.delete("/{snippet_id}")
def delete_snippet(snippet_id: int, current_user: dict = Depends(get_current_user)):
    """
    Deletes a snippet.
    Only the snippet owner or an administrator is authorized.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, title FROM snippets WHERE id = ?;", (snippet_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snippet with ID {snippet_id} not found."
            )

        # Authorization check: owner or admin
        if row["user_id"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have authorization to delete this snippet."
            )

        cursor.execute("DELETE FROM snippets WHERE id = ?;", (snippet_id,))

    return {
        "success": True,
        "message": f"Snippet '{row['title']}' deleted successfully."
    }
