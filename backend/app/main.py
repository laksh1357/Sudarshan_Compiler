"""
Main FastAPI Application Entry Point for Sudarshan Compiler Studio.
"""

import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import health, examples, compilation

app = FastAPI(
    title="Sudarshan Compiler Studio API",
    description="Backend API powering the interactive Sudarshan Compiler Studio web IDE.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
# Allows configurable origins for production while facilitating local development
cors_env = os.getenv("CORS_ORIGINS", "*")
if cors_env.strip() == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def check_payload_limit(request: Request, call_next):
    """Enforces request payload size limits (max 64KB) to mitigate DOS risks."""
    max_bytes = 65536  # 64 KB
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Payload too large. Source code must not exceed 64KB."}
                )
        except ValueError:
            pass

    return await call_next(request)


# Include Sub-Routers
app.include_router(health.router)
app.include_router(examples.router)
app.include_router(compilation.router)

# Also mount without /api prefix for serverless environments where /api is stripped by the gateway
app.include_router(health.router, prefix="")
app.include_router(examples.router, prefix="")
app.include_router(compilation.router, prefix="")

@app.get("/debug-path")
@app.get("/api/debug-path")
def debug_path(request: Request):
    return {
        "url_path": request.url.path,
        "scope_path": request.scope.get("path", ""),
        "headers": dict(request.headers)
    }

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Locate frontend distribution directory
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "Welcome to Sudarshan Compiler Studio API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "health": "/api/health",
                "examples": "/api/examples",
                "compile": "POST /api/compile",
                "compile_run": "POST /api/compile-run",
                "run": "POST /api/run"
            }
        }
