"""
Backend Test Suite for Sudarshan Compiler Studio API.
Uses FastAPI TestClient to test all endpoints, edge cases, error conditions,
pipeline stages, and execution safety.
"""

import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Sudarshan" in data["compiler"]
    assert len(data["supported_phases"]) == 6


def test_examples_endpoint():
    resp = client.get("/api/examples")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 7
    ids = [item["id"] for item in items]
    assert "valid-program" in ids
    assert "constant-folding" in ids
    assert "nested-scopes" in ids
    assert "error-syntax" in ids
    assert "error-semantic" in ids
    assert "error-lexical" in ids
    assert "error-runtime" in ids


def test_compile_valid_program():
    code = """
    int x = 10;
    int y = 20;
    print(x + y);
    """
    resp = client.post("/api/compile", json={"source_code": code, "optimize": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["failed_phase"] is None

    # Tokens check
    assert data["tokens"] is not None
    assert len(data["tokens"]) > 0

    # AST check
    assert data["ast"] is not None
    assert data["ast"]["type"] == "Program"
    assert "x" in data["ast_text"]

    # Symbol table check
    assert data["symbol_table"] is not None
    symbols = [s["name"] for s in data["symbol_table"]["symbols"]]
    assert "x" in symbols
    assert "y" in symbols

    # TAC check
    assert data["raw_tac"] is not None
    assert data["optimized_tac"] is not None
    assert len(data["raw_tac"]) > 0


def test_compile_and_run_valid_program():
    code = """
    int sum = 0;
    int i = 1;
    while (i <= 5) {
        sum = sum + i;
        i = i + 1;
    }
    print(sum);
    """
    resp = client.post("/api/compile-run", json={"source_code": code, "optimize": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["execution_status"] == "success"
    assert data["program_output"] == [15]
    assert "15" in data["stdout_text"]
    assert data["execution_steps"] is not None
    assert data["execution_steps"] > 0


def test_optimization_report_and_reduction():
    code = """
    int x = 2 + 3 * 4;
    int y = (10 - 2) * 5;
    print(x);
    print(y);
    """
    resp = client.post("/api/compile", json={"source_code": code, "optimize": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["optimization_stats"] is not None
    assert data["optimization_stats"]["transformations_count"] > 0
    assert len(data["optimization_report"]) > 0

    pass_names = [r["pass_name"] for r in data["optimization_report"]]
    assert "Constant Folding" in pass_names


def test_algebraic_optimization_report():
    code = """
    int x = 10;
    while (x > 0) {
        x = x + 0;
    }
    """
    resp = client.post("/api/compile", json={"source_code": code, "optimize": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    pass_names = [r["pass_name"] for r in data["optimization_report"]]
    assert "Algebraic Simplification" in pass_names


def test_lexical_error_no_fabricated_phases():
    code = "int x = @ 10;"
    resp = client.post("/api/compile", json={"source_code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["failed_phase"] == "lexical"
    assert len(data["compilation_errors"]) == 1
    assert data["compilation_errors"][0]["error_type"] == "LexerError"
    assert "@" in data["compilation_errors"][0]["message"]

    # No fabricated subsequent phase outputs
    assert data["ast"] is None
    assert data["symbol_table"] is None
    assert data["raw_tac"] is None
    assert data["optimized_tac"] is None


def test_syntax_error_no_fabricated_phases():
    code = "int x = 10\nprint(x);"
    resp = client.post("/api/compile", json={"source_code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["failed_phase"] == "syntax"
    assert len(data["compilation_errors"]) == 1
    assert data["compilation_errors"][0]["error_type"] == "ParserError"

    # Tokens exist, but AST and TAC must NOT be fabricated
    assert data["tokens"] is not None
    assert data["ast"] is None
    assert data["raw_tac"] is None


def test_semantic_error_no_fabricated_phases():
    code = "print(undeclared_var);"
    resp = client.post("/api/compile", json={"source_code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["failed_phase"] == "semantic"
    assert len(data["compilation_errors"]) == 1
    assert data["compilation_errors"][0]["error_type"] == "SemanticError"
    assert "undeclared_var" in data["compilation_errors"][0]["message"]

    # Tokens and AST exist, but TAC must NOT be fabricated
    assert data["tokens"] is not None
    assert data["ast"] is not None
    assert data["raw_tac"] is None


def test_runtime_division_by_zero():
    code = """
    int x = 42;
    int y = 0;
    print(x / y);
    """
    resp = client.post("/api/compile-run", json={"source_code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True  # Compilation succeeded
    assert data["execution_status"] == "error"
    assert len(data["runtime_errors"]) == 1
    assert "Division by zero" in data["runtime_errors"][0]["message"]


def test_execution_step_limit_infinite_loop():
    code = """
    int x = 1;
    while (x > 0) {
        x = x + 1;
    }
    """
    # Set step limit to 50
    resp = client.post("/api/compile-run", json={"source_code": code, "max_steps": 50})
    assert resp.status_code == 200
    data = resp.json()
    assert data["execution_status"] == "step_limit_exceeded"
    assert len(data["runtime_errors"]) == 1
    assert "step limit exceeded" in data["runtime_errors"][0]["message"].lower()


def test_empty_source_code_rejected():
    resp = client.post("/api/compile", json={"source_code": "   "})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_oversized_payload_rejected():
    oversized = "int x = 1;\n" * 6000  # > 64KB
    resp = client.post("/api/compile", json={"source_code": oversized})
    assert resp.status_code in (413, 422)


def test_end_to_end_full_pipeline_verification():
    """
    End-to-end integration test:
    Loads valid.mini, runs the entire 5-phase compiler + VM, and validates
    that all 8 stages produce consistent, non-fabricated data.
    """
    examples_resp = client.get("/api/examples")
    assert examples_resp.status_code == 200
    examples = examples_resp.json()
    valid_ex = next(ex for ex in examples if ex["filename"] == "valid.mini")

    resp = client.post("/api/compile-run", json={
        "source_code": valid_ex["source_code"],
        "optimize": True,
        "max_steps": 100000
    })
    assert resp.status_code == 200
    data = resp.json()

    # Phase 1: Tokens
    assert data["tokens"] is not None
    types = [t["type"] for t in data["tokens"]]
    assert "WHILE" in types
    assert "IF" in types
    assert "PRINT" in types

    # Phase 2: AST
    assert data["ast"] is not None
    assert data["ast"]["type"] == "Program"
    assert "Program:" in data["ast_text"]

    # Phase 3: Symbol Table
    assert data["symbol_table"] is not None
    symbols = [s["name"] for s in data["symbol_table"]["symbols"]]
    assert "sum" in symbols
    assert "i" in symbols
    assert "bonus" in symbols

    # Phase 4: Raw TAC
    assert data["raw_tac"] is not None
    raw_ops = [i["op"] for i in data["raw_tac"]]
    assert "ASSIGN" in raw_ops
    assert "PRINT" in raw_ops
    assert "LABEL" in raw_ops

    # Phase 4b: Optimized TAC
    assert data["optimized_tac"] is not None
    assert data["optimization_stats"] is not None

    # Phase 5: VM Output
    assert data["execution_status"] == "success"
    assert data["program_output"] == [15, 115]

