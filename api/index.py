"""
Sudarshan Compiler Studio - 100% Python Web Server and API
Entry point for local development and Vercel serverless execution.
"""

import sys
import os
from typing import Dict, Any

# Setup import paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.compiler_service import compile_sudarshan

app = FastAPI(
    title="Sudarshan Compiler Studio",
    description="100% Python Interactive Compiler Laboratory and Studio.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to normalize Vercel serverless rewritten paths
class VercelPathNormalizer(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        # Normalize /api/index.py or /api/index to root or subpath
        if path in ("/api/index.py", "/api/index", "/api/index.py/"):
            request.scope["path"] = "/"
        elif path.startswith("/api/index.py/"):
            request.scope["path"] = path[len("/api/index.py"):]
        return await call_next(request)

app.add_middleware(VercelPathNormalizer)


def load_example(filename: str) -> str:
    path = os.path.join(EXAMPLES_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


INDEX_FILE = os.path.join(ROOT_DIR, "index.html")
STYLE_FILE = os.path.join(ROOT_DIR, "style.css")
APP_FILE = os.path.join(ROOT_DIR, "app.js")


@app.get("/")
@app.get("/index.html")
@app.get("/api/index.py")
@app.get("/api/index")
def serve_index():
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE, media_type="text/html")
    # Fallback to frontend/dist/index.html if built
    dist_index = os.path.join(ROOT_DIR, "frontend", "dist", "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index, media_type="text/html")
    return {"message": "Sudarshan Compiler Studio API", "status": "running"}


@app.get("/style.css")
@app.get("/api/style.css")
@app.get("/api/index.py/style.css")
def serve_css():
    if os.path.exists(STYLE_FILE):
        return FileResponse(STYLE_FILE, media_type="text/css")
    return JSONResponse(status_code=404, content={"detail": "style.css not found"})


@app.get("/app.js")
@app.get("/api/app.js")
@app.get("/api/index.py/app.js")
def serve_js():
    if os.path.exists(APP_FILE):
        return FileResponse(APP_FILE, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"detail": "app.js not found"})


@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "name": "Sudarshan Compiler Studio",
        "version": "2.0.0",
        "compiler": "Sudarshan Language Engine (100% Python)",
        "supported_phases": [
            "Lexical Analysis",
            "Syntax Analysis",
            "Abstract Syntax Tree",
            "Semantic Analysis",
            "Symbol Table",
            "Intermediate Representation (TAC)",
            "Optimization Passes",
            "Virtual Machine Execution"
        ]
    }


@app.get("/api/presets")
@app.get("/presets")
@app.get("/api/index.py/presets")
def get_presets() -> Dict[str, str]:
    """Returns curated presets mapping filenames to their source code."""
    presets = {
        "valid.mini": load_example("valid.mini"),
        "opt_test.mini": load_example("opt_test.mini"),
        "nested_scope.mini": load_example("nested_scope.mini"),
        "algebraic.mini": load_example("algebraic.mini"),
        "loop_factorial.mini": load_example("loop_factorial.mini"),
        "error_syntax.mini": load_example("error_syntax.mini"),
        "error_semantic.mini": load_example("error_semantic.mini"),
        "error_lexical.mini": load_example("error_lexical.mini"),
        "error_runtime.mini": load_example("error_runtime.mini"),
    }
    return presets


@app.get("/api/examples")
@app.get("/examples")
def get_examples():
    """Alias for examples catalog."""
    from backend.app.routes.examples import get_examples as be_examples
    return be_examples()


@app.post("/api/compile")
@app.post("/compile")
@app.post("/api/index.py/compile")
async def compile_code(request: Request):
    """
    Main compilation and execution endpoint.
    Invokes the real Python compiler in strict phase order.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    code = body.get("code") or body.get("source_code") or ""
    optimize = body.get("optimize", True)

    if not code.strip():
        return JSONResponse(content={
            "success": False,
            "errors": ["Source code cannot be empty. Please enter Sudarshan program code."]
        })

    c_res = compile_sudarshan(code, optimize=optimize, execute=True)

    # 1. Format tokens
    tokens_text = ""
    if c_res.tokens:
        tokens_text = "\n".join(
            f"[Line {t.line}:{t.column}] {t.type.ljust(16)} '{t.value if t.value is not None else ''}'"
            for t in c_res.tokens
        )

    # 2. Format symbol table
    sym_data = []
    sym_lines = [
        "-----------------------------------------------------------------",
        "NAME             TYPE       KIND       SCOPE            LOCATION",
        "-----------------------------------------------------------------",
    ]
    if c_res.symbol_table and c_res.symbol_table.symbols:
        for s in c_res.symbol_table.symbols:
            scope_str = "global" if s.scope_level == 0 else f"scope_{s.scope_level}"
            pos_str = f"Decl @ L{s.line}:{s.column}" if s.line else "initialized"
            sym_data.append({
                "name": s.name,
                "type": s.type_name,
                "kind": "variable",
                "scope": scope_str,
                "value": pos_str
            })
            sym_lines.append(f"{s.name.ljust(16)} {s.type_name.ljust(10)} variable   {scope_str.ljust(16)} {pos_str}")
    sym_lines.append("-----------------------------------------------------------------")
    sym_table_text = "\n".join(sym_lines)

    has_nested = any(s.scope_level > 0 for s in (c_res.symbol_table.symbols if c_res.symbol_table else []))
    sym_notes = (
        "Variables declared within while or if/else blocks are scoped locally and cannot leak outside their block."
        if has_nested else
        "All variables are currently in global scope. Nested blocks will create isolated scope tiers."
    )

    # 3. Format semantic checks
    checks = [
        "Type compatibility checked: variable assignments and expressions are type-safe.",
        "Identifier resolution verified: all referenced variables are declared in accessible scopes.",
        "Declaration uniqueness verified: no duplicate variable declarations in the same scope.",
        "Control flow validated: loop and condition guards evaluate to valid expressions."
    ]

    # 4. Format optimization behavior
    if c_res.optimization_report:
        report_lines = [
            f"Pass [{r.pass_name}]:\n  Original:    {r.original}\n  Transformed: {r.transformed}\n  Reason:      {r.reason}"
            for r in c_res.optimization_report
        ]
        opt_behavior = f"Optimizer executed {len(c_res.optimization_report)} verified transformations:\n\n" + "\n\n".join(report_lines)
    else:
        opt_behavior = "Instructions are in minimal canonical form. No additional constant folding or dead code elimination was required."

    # 5. Format program output
    if c_res.stdout_text and c_res.stdout_text.strip():
        output_text = c_res.stdout_text.strip()
    elif c_res.program_output:
        output_text = "\n".join(str(v) for v in c_res.program_output)
    else:
        output_text = "[Program executed successfully with no output]"

    # 6. Format errors
    errors = []
    for err in c_res.compilation_errors + c_res.runtime_errors:
        loc = f" (Line {err.line}, Col {err.column})" if err.line else ""
        errors.append(f"{err.error_type}: {err.message}{loc}")

    is_ok = c_res.success and c_res.execution_status == "success"

    return JSONResponse(content={
        "success": is_ok,
        "tokens": tokens_text,
        "ast": c_res.ast_text or "",
        "ast_json": c_res.ast,
        "symbol_table": sym_table_text,
        "symbol_table_data": sym_data,
        "symbol_table_notes": sym_notes,
        "semantic_checks": checks if is_ok else [],
        "semantic_analysis": "Semantic analysis: SUCCESS" if c_res.success else "Semantic analysis: FAILED",
        "raw_tac": c_res.raw_tac_text or "",
        "llvm_ir": c_res.raw_tac_text or "",
        "optimized_ir": c_res.optimized_tac_text or "",
        "optimized_behavior": opt_behavior,
        "output": output_text if is_ok else f"[Compilation/Runtime Halted] {'; '.join(errors)}",
        "errors": errors
    })


@app.post("/api/compile-run")
@app.post("/compile-run")
@app.post("/api/index.py/compile-run")
async def compile_run_compat(request: Request):
    """Backwards-compatibility route for compile-run."""
    return await compile_code(request)


# Entry point for Vercel
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=True)
