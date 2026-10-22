"""
Database connectivity and management module for Sudarshan Compiler Studio.
Provides SQLite connection management, auto-initialization, schema migrations,
CRUD operations, and transaction safety.
"""

import os
import sqlite3
import datetime
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def get_db_path() -> str:
    """
    Determines the database file path.
    Prioritizes DATABASE_PATH / DATABASE_URL environment variables.
    Falls back to /tmp on Vercel or read-only filesystems.
    """
    env_path = os.getenv("DATABASE_PATH") or os.getenv("DATABASE_URL")
    if env_path:
        if env_path.startswith("sqlite:///"):
            return env_path[len("sqlite:///"):]
        return env_path

    # On Vercel serverless environment or if root directory is read-only
    if os.getenv("VERCEL") or not os.access(ROOT_DIR, os.W_OK):
        return "/tmp/sudarshan.db"

    return os.path.join(ROOT_DIR, "sudarshan.db")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for acquiring a database connection with row factory
    and automatic commit / rollback transaction handling.
    """
    db_path = get_db_path()
    # Ensure parent directory exists
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            pass

    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initializes database schema and seeds default administrative and developer accounts.
    Idempotent: safe to run multiple times.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Users table (Authentication & Authorization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            );
        """)

        # 2. Code Snippets table (Database CRUD operations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                language TEXT NOT NULL DEFAULT 'sudarshan',
                code TEXT NOT NULL,
                is_public INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 3. Compilation History table (Audit & execution tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compilation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                language TEXT NOT NULL,
                code_snippet TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # Create indexes for optimal query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_user ON snippets(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_public ON snippets(is_public);")

    # Seed initial accounts if table is empty
    seed_default_users()


def seed_default_users() -> None:
    """
    Seeds default admin and developer users if none exist.
    Password hashing is imported lazily to avoid circular dependencies.
    """
    from backend.app.auth import hash_password

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
        if count == 0:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Seed 1: Administrator
            admin_pwd_hash, admin_salt = hash_password("Admin@123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, ("admin", "admin@sudarshan.org", admin_pwd_hash, admin_salt, "admin", now))

            # Seed 2: Standard Developer User
            dev_pwd_hash, dev_salt = hash_password("Dev@123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, ("developer", "dev@sudarshan.org", dev_pwd_hash, dev_salt, "user", now))

            admin_id = 1
            # Seed sample snippets for demonstration
            cursor.execute("""
                INSERT INTO snippets (user_id, title, description, language, code, is_public, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                admin_id,
                "Factorial Calculation",
                "Recursive factorial in Sudarshan language",
                "sudarshan",
                "int n = 5;\nint fact = 1;\nwhile (n > 1) {\n    fact = fact * n;\n    n = n - 1;\n}\nprint(fact);",
                1,
                now,
                now
            ))

            cursor.execute("""
                INSERT INTO snippets (user_id, title, description, language, code, is_public, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                admin_id,
                "Python Quick Sort",
                "Classic divide-and-conquer sorting algorithm in Python",
                "python",
                "def quicksort(arr):\n    if len(arr) <= 1: return arr\n    p = arr[0]\n    return quicksort([x for x in arr[1:] if x <= p]) + [p] + quicksort([x for x in arr[1:] if x > p])\n\nprint(quicksort([7, 2, 9, 1, 5]))\n",
                1,
                now,
                now
            ))


def get_db_health() -> Dict[str, Any]:
    """
    Checks database connection health and statistics.
    Returns status, engine, path, and table row counts.
    """
    try:
        db_path = get_db_path()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.execute("SELECT COUNT(*) FROM users;")
            users_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM snippets;")
            snippets_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM compilation_history;")
            history_count = cursor.fetchone()[0]

            return {
                "status": "connected",
                "dialect": "sqlite3",
                "database_path": db_path,
                "tables": {
                    "users": users_count,
                    "snippets": snippets_count,
                    "compilation_history": history_count
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "dialect": "sqlite3",
            "error": str(e)
        }
