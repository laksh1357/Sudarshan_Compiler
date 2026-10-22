"""
Database health and connectivity inspection router.
"""

from fastapi import APIRouter
from backend.app.db import get_db_health

router = APIRouter(prefix="/db", tags=["Database Connectivity"])


@router.get("/health")
def database_health():
    """
    Returns connection health and table status of the underlying database.
    """
    return get_db_health()
