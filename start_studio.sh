#!/usr/bin/env bash
# Sudarshan Compiler Studio Development Server Launcher (100% Python)
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

echo "Starting Sudarshan Compiler Studio on http://127.0.0.1:8000 ..."
$UVICORN_BIN api.index:app --host 127.0.0.1 --port 8000 --reload
