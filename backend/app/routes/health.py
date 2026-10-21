"""
Health and Status Route for Sudarshan Compiler Studio.
"""

from fastapi import APIRouter
from backend.app.schemas import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns backend status, compiler availability, and supported pipeline phases."""
    return HealthResponse(
        status="ok",
        name="Sudarshan Compiler Studio",
        version="1.0.0",
        compiler="Sudarshan (MiniLang)",
        supported_phases=[
            "Lexical Analysis (Scanner)",
            "Syntax Analysis (LL(1) Recursive Descent Parser)",
            "Semantic Analysis (Lexical Scopes & Symbol Table)",
            "Intermediate Code Generation (Three-Address Code)",
            "Intermediate Code Optimization (Constant Folding, Propagation & DCE)",
            "Virtual Machine Execution (TAC Interpreter)"
        ]
    )
