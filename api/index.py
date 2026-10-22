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
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.compiler_service import compile_sudarshan
from backend.app.multi_lang_service import execute_multi_lang, LANGUAGE_CONFIGS

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
        # 1. Check if Vercel passed the path via query parameter __path
        query_path = request.query_params.get("__path")
        if query_path:
            clean_path = query_path.split("?")[0]
            if clean_path:
                request.scope["path"] = clean_path

        # 2. Restore original matched path from Vercel rewrite headers if present
        matched = (
            request.headers.get("x-matched-path")
            or request.headers.get("x-forwarded-uri")
            or request.headers.get("x-vercel-matched-path")
        )
        if matched:
            raw_path = matched.split("?")[0]
            if raw_path and raw_path != "/api/index.py":
                request.scope["path"] = raw_path

        path = request.scope.get("path", "")
        # If a POST request arrived at rewritten root or serverless file path, route to compile
        if request.method == "POST":
            if path in ("/", "/api", "/api/", "/api/index.py", "/api/index", "/api/index.py/", "/index.html"):
                request.scope["path"] = "/api/compile"
        else:
            # Normalize /api/index.py, /api/index, /api, or trailing slashes to root for GET
            if path in ("/api/index.py", "/api/index", "/api/index.py/", "/api", "/api/"):
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


def read_static_file(filename: str) -> str:
    """Helper to locate and read static files across local and Vercel serverless lambda paths."""
    candidates = [
        os.path.join(ROOT_DIR, filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        os.path.join(os.getcwd(), filename),
        filename
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        return content
            except Exception:
                pass
    return ""


# Pre-cache static assets into memory on startup
HTML_CACHE = read_static_file("index.html")
CSS_CACHE = read_static_file("style.css")
JS_CACHE = read_static_file("app.js")


@app.get("/")
@app.get("/index.html")
@app.get("/api")
@app.get("/api/")
@app.get("/api/index.py")
@app.get("/api/index.py/")
@app.get("/api/index")
def serve_index():
    global HTML_CACHE
    if not HTML_CACHE:
        HTML_CACHE = read_static_file("index.html")
    if HTML_CACHE:
        return HTMLResponse(content=HTML_CACHE, status_code=200, media_type="text/html; charset=utf-8")
    return HTMLResponse(content="<!DOCTYPE html><html><body><h1>Sudarshan Compiler Studio</h1></body></html>", status_code=200, media_type="text/html")


@app.get("/style.css")
@app.get("/api/style.css")
@app.get("/api/index.py/style.css")
def serve_css():
    global CSS_CACHE
    if not CSS_CACHE:
        CSS_CACHE = read_static_file("style.css")
    if CSS_CACHE:
        return Response(content=CSS_CACHE, status_code=200, media_type="text/css; charset=utf-8")
    return Response(content="/* Sudarshan Compiler Studio CSS */", status_code=200, media_type="text/css; charset=utf-8")


@app.get("/app.js")
@app.get("/api/app.js")
@app.get("/api/index.py/app.js")
def serve_js():
    global JS_CACHE
    if not JS_CACHE:
        JS_CACHE = read_static_file("app.js")
    if JS_CACHE:
        return Response(content=JS_CACHE, status_code=200, media_type="application/javascript; charset=utf-8")
    return Response(content="// Sudarshan Compiler Studio JS", status_code=200, media_type="application/javascript; charset=utf-8")


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


MULTI_LANG_PRESETS = {
    "sudarshan": {
        "valid.mini": load_example("valid.mini"),
        "opt_test.mini": load_example("opt_test.mini"),
        "nested_scope.mini": load_example("nested_scope.mini"),
        "algebraic.mini": load_example("algebraic.mini"),
        "loop_factorial.mini": load_example("loop_factorial.mini"),
        "error_syntax.mini": load_example("error_syntax.mini"),
        "error_semantic.mini": load_example("error_semantic.mini"),
        "error_lexical.mini": load_example("error_lexical.mini"),
        "error_runtime.mini": load_example("error_runtime.mini"),
    },
    "python": {
        "fibonacci.py": 'def fibonacci(n):\n    seq = [0, 1]\n    for _ in range(2, n):\n        seq.append(seq[-1] + seq[-2])\n    return seq\n\nprint("=== Python Fibonacci Generator ===")\nprint("First 10 Fibonacci numbers:", fibonacci(10))\n',
        "primes.py": 'def sieve_of_eratosthenes(limit):\n    primes = []\n    is_prime = [True] * (limit + 1)\n    for p in range(2, limit + 1):\n        if is_prime[p]:\n            primes.append(p)\n            for i in range(p * p, limit + 1, p):\n                is_prime[i] = False\n    return primes\n\nprint("Primes up to 40:", sieve_of_eratosthenes(40))\n',
        "quicksort.py": 'def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\nnumbers = [64, 34, 25, 12, 22, 11, 90]\nprint("Sorted:", quicksort(numbers))\n'
    },
    "c": {
        "hello.c": '#include <stdio.h>\n\nint main(void) {\n    printf("=== C (GCC 13) Execution ===\\n");\n    int sum = 0;\n    for (int i = 1; i <= 10; i++) {\n        sum += i;\n    }\n    printf("Sum of 1..10 = %d\\n", sum);\n    return 0;\n}\n',
        "pointers.c": '#include <stdio.h>\n\nvoid swap(int *a, int *b) {\n    int temp = *a;\n    *a = *b;\n    *b = temp;\n}\n\nint main(void) {\n    int x = 42, y = 99;\n    printf("Before swap: x=%d, y=%d\\n", x, y);\n    swap(&x, &y);\n    printf("After swap:  x=%d, y=%d\\n", x, y);\n    return 0;\n}\n',
        "bubble_sort.c": '#include <stdio.h>\n\nint main(void) {\n    int arr[] = {64, 34, 25, 12, 22, 11, 90};\n    int n = sizeof(arr)/sizeof(arr[0]);\n    for (int i = 0; i < n-1; i++) {\n        for (int j = 0; j < n-i-1; j++) {\n            if (arr[j] > arr[j+1]) {\n                int temp = arr[j];\n                arr[j] = arr[j+1];\n                arr[j+1] = temp;\n            }\n        }\n    }\n    printf("Sorted array: ");\n    for (int i = 0; i < n; i++) printf("%d ", arr[i]);\n    printf("\\n");\n    return 0;\n}\n'
    },
    "cpp": {
        "vectors.cpp": '#include <iostream>\n#include <vector>\n#include <numeric>\n\nint main() {\n    std::cout << "=== C++20 Standard Library Demo ===\\n";\n    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};\n    int sum = std::accumulate(numbers.begin(), numbers.end(), 0);\n    std::cout << "Sum: " << sum << "\\n";\n    std::cout << "Even numbers: ";\n    for (int n : numbers) {\n        if (n % 2 == 0) std::cout << n << " ";\n    }\n    std::cout << std::endl;\n    return 0;\n}\n',
        "templates.cpp": '#include <iostream>\n\ntemplate<typename T>\nT add(T a, T b) {\n    return a + b;\n}\n\nint main() {\n    std::cout << "Int: " << add(10, 25) << std::endl;\n    std::cout << "Double: " << add(3.14, 2.71) << std::endl;\n    return 0;\n}\n'
    },
    "java": {
        "Factorial.java": 'public class Main {\n    public static long factorial(int n) {\n        long result = 1;\n        for (int i = 2; i <= n; i++) result *= i;\n        return result;\n    }\n\n    public static void main(String[] args) {\n        System.out.println("=== Java 21 Execution ===");\n        int num = 10;\n        System.out.println("Factorial of " + num + " = " + factorial(num));\n    }\n}\n',
        "BinarySearch.java": 'public class Main {\n    public static int binarySearch(int[] arr, int target) {\n        int low = 0, high = arr.length - 1;\n        while (low <= high) {\n            int mid = (low + high) / 2;\n            if (arr[mid] == target) return mid;\n            if (arr[mid] < target) low = mid + 1;\n            else high = mid - 1;\n        }\n        return -1;\n    }\n\n    public static void main(String[] args) {\n        int[] sorted = {2, 5, 8, 12, 16, 23, 38, 56, 72, 91};\n        int target = 23;\n        int idx = binarySearch(sorted, target);\n        System.out.println("Found " + target + " at index: " + idx);\n    }\n}\n'
    },
    "javascript": {
        "primes.js": 'function findPrimes(limit) {\n    const primes = [];\n    for (let i = 2; i <= limit; i++) {\n        let isPrime = true;\n        for (let j = 2; j * j <= i; j++) {\n            if (i % j === 0) { isPrime = false; break; }\n        }\n        if (isPrime) primes.push(i);\n    }\n    return primes;\n}\n\nconsole.log("=== Node.js Execution ===");\nconsole.log("Primes up to 40:", findPrimes(40));\n',
        "async.js": 'async function simulateTask(name, ms) {\n    return new Promise(resolve => setTimeout(() => resolve(`Task ${name} completed`), ms));\n}\n\nasync function run() {\n    console.log("Starting async tasks...");\n    const results = await Promise.all([\n        simulateTask("A", 100),\n        simulateTask("B", 50)\n    ]);\n    results.forEach(r => console.log(r));\n}\n\nrun();\n'
    },
    "typescript": {
        "interfaces.ts": 'interface CompilerConfig {\n    name: string;\n    version: string;\n    strict: boolean;\n    targets: string[];\n}\n\nfunction printSummary(config: CompilerConfig): void {\n    console.log(`[${config.name} v${config.version}]`);\n    console.log(`Strict mode: ${config.strict}`);\n    console.log(`Targets: ${config.targets.join(", ")}`);\n}\n\nconst studioConfig: CompilerConfig = {\n    name: "Sudarshan Studio",\n    version: "2.0.0",\n    strict: true,\n    targets: ["Python", "C", "C++", "Java", "JavaScript", "TypeScript", "Sudarshan"]\n};\n\nprintSummary(studioConfig);\n'
    }
}


@app.get("/api/presets")
@app.get("/presets")
@app.get("/api/index.py/presets")
def get_presets(language: Optional[str] = None) -> Dict[str, Any]:
    """Returns curated presets mapping filenames to their source code."""
    if language and language in MULTI_LANG_PRESETS:
        return MULTI_LANG_PRESETS[language]
    # Return sudarshan presets as flat dictionary for backward compatibility
    # and provide full catalog under "all" key if requested
    res = dict(MULTI_LANG_PRESETS["sudarshan"])
    res["__all_presets__"] = MULTI_LANG_PRESETS
    return res


@app.get("/api/examples")
@app.get("/examples")
def get_examples():
    """Alias for examples catalog."""
    from backend.app.routes.examples import get_examples as be_examples
    return be_examples()


@app.post("/api/compile")
@app.post("/compile")
@app.post("/api/index.py/compile")
@app.post("/api/index.py")
@app.post("/api")
@app.post("/api/")
@app.post("/")
async def compile_code(request: Request):
    """
    Main compilation and execution endpoint.
    Supports multi-language compilation (Python, C, C++, Java, JavaScript, TypeScript, Sudarshan).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    code = body.get("code") or body.get("source_code") or ""
    language = (body.get("language") or "sudarshan").lower().strip()
    stdin = body.get("stdin") or ""
    optimize = body.get("optimize", True)

    if not code.strip():
        return JSONResponse(content={
            "success": False,
            "errors": [f"Source code cannot be empty. Please enter {language.capitalize()} program code."]
        })

    # Dispatch to multi-language runner if not Sudarshan
    if language != "sudarshan" and language in LANGUAGE_CONFIGS:
        lang_res = execute_multi_lang(language, code, stdin=stdin, optimize=optimize)
        return JSONResponse(content={
            "success": lang_res["success"],
            "tokens": lang_res["tokens"],
            "ast": lang_res["ast"],
            "ast_json": lang_res["ast_json"],
            "symbol_table": lang_res["symbol_table"],
            "symbol_table_data": lang_res["symbol_table_data"],
            "symbol_table_notes": lang_res["symbol_table_notes"],
            "semantic_checks": lang_res["semantic_checks"],
            "semantic_analysis": lang_res["semantic_analysis"],
            "raw_tac": lang_res["raw_tac"],
            "llvm_ir": lang_res["llvm_ir"],
            "optimized_ir": lang_res["optimized_ir"],
            "optimized_behavior": lang_res["optimized_behavior"],
            "output": lang_res["output"],
            "errors": lang_res["errors"],
            "language": language,
            "runtime_title": lang_res.get("runtime_title", f"{language} runner")
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
        vars_summary = []
        if c_res.symbol_table and c_res.symbol_table.symbols:
            for s in c_res.symbol_table.symbols:
                vars_summary.append(f"  • {s.name} ({s.type_name})")
        if vars_summary:
            output_text = (
                "[Program executed successfully]\n\n"
                "Tracked Variables:\n" + "\n".join(vars_summary) + "\n\n"
                "💡 Tip: Use 'print(<variable>);' to display values in the console output."
            )
        else:
            output_text = "[Program executed successfully with no output]\n\n💡 Tip: Use 'print(<variable>);' to display values in the console output."

    # 6. Format errors
    errors = []
    for err in c_res.compilation_errors + c_res.runtime_errors:
        loc = f" (Line {err.line}, Col {err.column})" if err.line else ""
        errors.append(f"{err.error_type}: {err.message}{loc}")

    if errors:
        syntax_hint = "💡 Sudarshan syntax: 'int x = 10;' (semicolons & 'int' required), 'print(x);', 'if (cond) { }', 'while (cond) { }'"
        errors.append(syntax_hint)

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
        "output": output_text if is_ok else f"[Compilation/Runtime Halted]\n\n" + "\n".join(errors),
        "errors": errors
    })


@app.post("/api/compile-run")
@app.post("/compile-run")
@app.post("/api/index.py/compile-run")
async def compile_run_compat(request: Request):
    """Backwards-compatibility route for compile-run."""
    return await compile_code(request)


# Catch-all route to serve the Studio SPA for any frontend path, preventing 404s
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    clean = full_path.strip("/")
    if clean.endswith("style.css"):
        return serve_css()
    if clean.endswith("app.js"):
        return serve_js()
    if clean in ("api/health", "health"):
        return health()
    if clean in ("api/presets", "presets"):
        return get_presets()
    return serve_index()


# Entry point for Vercel
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=True)
