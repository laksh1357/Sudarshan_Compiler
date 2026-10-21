#!/usr/bin/env bash
# Sudarshan Compiler Studio Development Server Launcher
set -e

echo "=================================================="
echo "    SUDARSHAN COMPILER STUDIO - LOCAL LAUNCHER    "
echo "=================================================="

# Check Python environment
if [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/python"
    UVICORN_BIN=".venv/bin/uvicorn"
else
    PYTHON_BIN="python3"
    UVICORN_BIN="uvicorn"
fi

echo "1. Starting FastAPI Backend on http://127.0.0.1:8000 ..."
$UVICORN_BIN backend.app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

echo "2. Starting Vite Frontend on http://localhost:5173 ..."
cd frontend && npm run dev
