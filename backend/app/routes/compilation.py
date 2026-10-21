"""
Compilation and Execution Routes for Sudarshan Compiler Studio.
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.schemas import (
    CompileRequest, CompileRunRequest, RunRequest, CompilationResponse
)
from backend.app.compiler_service import compile_sudarshan

router = APIRouter(prefix="/api", tags=["Compilation"])


@router.post("/compile", response_model=CompilationResponse)
def compile_code(req: CompileRequest) -> CompilationResponse:
    """
    Compiles Sudarshan source code through all pipeline stages
    (Lexer -> Parser -> Semantic Analyzer -> TAC -> Optimizer).
    Does not execute the program in the Virtual Machine.
    """
    if len(req.source_code.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code cannot be empty."
        )

    return compile_sudarshan(
        source_code=req.source_code,
        optimize=req.optimize,
        max_steps=req.max_steps,
        execute=False
    )


@router.post("/compile-run", response_model=CompilationResponse)
def compile_and_run_code(req: CompileRunRequest) -> CompilationResponse:
    """
    Compiles Sudarshan source code and executes the resulting
    optimized Three-Address Code within the Sudarshan Virtual Machine.
    """
    if len(req.source_code.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code cannot be empty."
        )

    return compile_sudarshan(
        source_code=req.source_code,
        optimize=req.optimize,
        max_steps=req.max_steps,
        execute=True
    )


@router.post("/run", response_model=CompilationResponse)
def run_code(req: RunRequest) -> CompilationResponse:
    """
    Executes compiled code in the Virtual Machine.
    Accepts source code to compile and run.
    """
    if not req.source_code or len(req.source_code.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code must be provided to run."
        )

    return compile_sudarshan(
        source_code=req.source_code,
        optimize=True,
        max_steps=req.max_steps,
        execute=True
    )
