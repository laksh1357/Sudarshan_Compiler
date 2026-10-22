"""
Tests for Multi-Language Execution Endpoint (/api/compile).
Verifies that Python, C, C++, Java, JavaScript, TypeScript, and Sudarshan
can be compiled and run with appropriate output, tokens, AST, and symbol tables.
"""

import pytest
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_presets_all_languages():
    resp = client.get("/api/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert "__all_presets__" in data
    all_presets = data["__all_presets__"]
    assert "python" in all_presets
    assert "c" in all_presets
    assert "cpp" in all_presets
    assert "java" in all_presets
    assert "javascript" in all_presets
    assert "typescript" in all_presets
    assert "sudarshan" in all_presets


def test_python_compile_and_run():
    payload = {
        "language": "python",
        "code": "print('Test Python Runner', 5 * 10)",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "Test Python Runner 50" in data["output"]
    assert data["tokens"] is not None and len(data["tokens"]) > 0
    assert data["ast"] is not None
    assert "python3" in data.get("runtime_title", "")


def test_javascript_compile_and_run():
    payload = {
        "language": "javascript",
        "code": "console.log('JS Result:', 12 + 34);",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "JS Result: 46" in data["output"]
    assert data["tokens"] is not None


def test_c_compile_and_run():
    payload = {
        "language": "c",
        "code": "#include <stdio.h>\nint main() { printf(\"C Math: %d\\n\", 20 + 22); return 0; }\n",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "C Math: 42" in data["output"]


def test_cpp_compile_and_run():
    payload = {
        "language": "cpp",
        "code": "#include <iostream>\nint main() { std::cout << \"CPP Sum: \" << 10 + 20 << std::endl; return 0; }\n",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "CPP Sum: 30" in data["output"]


def test_java_compile_and_run():
    payload = {
        "language": "java",
        "code": "public class Main { public static void main(String[] args) { System.out.println(\"Java Output: \" + (6 * 7)); } }\n",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "Java Output: 42" in data["output"]


def test_typescript_compile_and_run():
    payload = {
        "language": "typescript",
        "code": "const answer: number = 42;\nconsole.log(\"TS Output:\", answer);\n",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "TS Output: 42" in data["output"]


def test_sudarshan_preserved():
    payload = {
        "language": "sudarshan",
        "code": "int a = 15; int b = 25; print(a + b);",
        "optimize": True
    }
    resp = client.post("/api/compile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "40" in data["output"]
    assert "int" in data["symbol_table"]
