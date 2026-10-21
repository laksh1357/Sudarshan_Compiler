"""
Example Programs Route for Sudarshan Compiler Studio.
"""

import os
from typing import List, Dict
from fastapi import APIRouter
from backend.app.schemas import ExampleItem

router = APIRouter(tags=["Examples"])

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../examples"))

# Metadata mapping for repository examples
EXAMPLE_METADATA: Dict[str, Dict[str, str]] = {
    "valid.mini": {
        "id": "valid-program",
        "name": "Full Language Tour",
        "category": "Complete Program",
        "description": "Comprehensive demonstration of variables, while loops, condition branching, arithmetic, and console output.",
        "expected_output": "15\n115"
    },
    "opt_test.mini": {
        "id": "constant-folding",
        "name": "Constant Folding & Arithmetic",
        "category": "Optimization",
        "description": "Demonstrates compile-time expression evaluation for arithmetic: 2 + 3 * 4 -> 14 and (10 - 2) * 5 -> 40.",
        "expected_output": "14\n40"
    },
    "nested_scope.mini": {
        "id": "nested-scopes",
        "name": "Nested Scopes & Variable Shadowing",
        "category": "Scoping",
        "description": "Demonstrates block scopes ({ ... }), parent variable resolution, local variable shadowing, and scope exit isolation.",
        "expected_output": "30\n200\n10"
    },
    "algebraic.mini": {
        "id": "algebraic-simplification",
        "name": "Algebraic Identity Simplification",
        "category": "Optimization",
        "description": "Demonstrates algebraic identity reductions: x + 0 -> x, x * 1 -> x, x - x -> 0, x * 0 -> 0, x / 1 -> x.",
        "expected_output": "42\n42\n0\n0\n42"
    },
    "loop_factorial.mini": {
        "id": "loop-factorial",
        "name": "Factorial Calculator (Loops)",
        "category": "Algorithms",
        "description": "Calculates factorial of 5 (120) using while loop iteration and variable assignments.",
        "expected_output": "120"
    },
    "error_syntax.mini": {
        "id": "error-syntax",
        "name": "Syntax Error Diagnostic Demo",
        "category": "Diagnostics",
        "description": "Demonstrates parser syntax error detection when a required semicolon is missing.",
        "expected_output": "ParserError at line 6, column 1"
    },
    "error_semantic.mini": {
        "id": "error-semantic",
        "name": "Semantic Undeclared Variable Error",
        "category": "Diagnostics",
        "description": "Demonstrates semantic analyzer detection of assignment to an undeclared identifier.",
        "expected_output": "SemanticError at line 6, column 1"
    },
    "error_lexical.mini": {
        "id": "error-lexical",
        "name": "Lexical Scanner Error Demo",
        "category": "Diagnostics",
        "description": "Demonstrates lexer diagnostic handling when encountering an illegal character ('@').",
        "expected_output": "LexerError at line 6, column 9"
    },
    "error_runtime.mini": {
        "id": "error-runtime",
        "name": "VM Division-by-Zero Runtime Error",
        "category": "Diagnostics",
        "description": "Demonstrates safe virtual machine runtime trap when dividing an integer by zero.",
        "expected_output": "CompilerRuntimeError: Division by zero."
    }
}


@router.get("/examples", response_model=List[ExampleItem])
def get_examples() -> List[ExampleItem]:
    """Returns curated example programs loaded from the repository."""
    items: List[ExampleItem] = []

    for filename, meta in EXAMPLE_METADATA.items():
        file_path = os.path.join(EXAMPLES_DIR, filename)
        code = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        else:
            # Inline fallback for synthetic examples if file not yet written to disk
            if filename == "algebraic.mini":
                code = """// Algebraic Identity Simplification Demo
// Demonstrates x + 0, x * 1, x - x, x * 0, x / 1
int x = 42;
int a = x + 0;
int b = x * 1;
int c = x - x;
int d = x * 0;
int e = x / 1;
print(a);
print(b);
print(c);
print(d);
print(e);
"""
            elif filename == "loop_factorial.mini":
                code = """// Factorial Computation in Sudarshan
int n = 5;
int fact = 1;

while (n > 1) {
    fact = fact * n;
    n = n - 1;
}

print(fact);
"""

        items.append(ExampleItem(
            id=meta["id"],
            name=meta["name"],
            category=meta["category"],
            description=meta["description"],
            filename=filename,
            source_code=code,
            expected_output=meta.get("expected_output")
        ))

    return items
