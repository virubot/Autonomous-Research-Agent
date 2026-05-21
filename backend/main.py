from __future__ import annotations

import os
import sys

if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if homebrew_lib not in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", ""):
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{homebrew_lib}:{os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')}".strip(":")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.agent.executor import AgentExecutor
from backend.mcp import MCPServer
from backend.routes.generate import router as generate_router
from backend.routes.upload import router as upload_router
from backend.utils.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    mcp_server = MCPServer(enabled=settings.mcp_enabled)
    executor = AgentExecutor(settings=settings, mcp_server=mcp_server)

    app = FastAPI(
        title="Autonomous Research Assistant API",
        version="2.0.0",
    )

    # ── Exception Handlers (Prevent Raw Stack Traces) ──
    from fastapi.responses import JSONResponse
    from fastapi import Request, HTTPException
    import logging

    logger = logging.getLogger("backend.errors")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error("HTTP Exception on %s %s: status_code=%d detail=%r", request.method, request.url.path, exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.status_code,
                "detail": exc.detail,
                "message": exc.detail,
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled Exception on %s %s: %s", request.method, request.url.path, exc)
        message = str(exc)
        # Avoid leaking internal system details on generic system errors
        if "pdflatex" in message.lower() or "latex" in message.lower():
            friendly_detail = "PDF rendering failed. This is typically caused by LaTeX syntax errors or temporary compilation limits. The structured paper data is still fully intact."
        else:
            friendly_detail = f"An internal assistant error occurred: {message}"

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": 500,
                "detail": friendly_detail,
                "message": friendly_detail,
            }
        )

    # ── Logging Middleware ──
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import time
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info("%s %s completed in %.2fs with status %d", request.method, request.url.path, duration, response.status_code)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.executor = executor
    app.state.mcp_server = mcp_server

    @app.on_event("startup")
    def startup() -> None:
        for name, description, schema in [
            (
                "web_search",
                "Search the web for relevant context and citations.",
                {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}},
            ),
            (
                "extract_pdf",
                "Extract text from an uploaded PDF.",
                {"type": "object", "properties": {"file_path": {"type": "string"}}},
            ),
            (
                "extract_image",
                "Extract OCR text from an uploaded image.",
                {"type": "object", "properties": {"file_path": {"type": "string"}}},
            ),
            (
                "save_to_db",
                "Persist execution data into the unified memory store.",
                {"type": "object", "properties": {"data": {"type": "object"}}},
            ),
            (
                "upload_to_drive",
                "Upload generated output to Google Drive and return a shareable link.",
                {"type": "object", "properties": {"file_path": {"type": "string"}}},
            ),
        ]:
            mcp_server.register_tool(
                name=name,
                description=description,
                input_schema=schema,
                handler=lambda payload, tool=name: executor.execute_tool(
                    tool,
                    payload,
                    tool_mode="direct",
                ),
            )
        mcp_server.start()
        if settings.strict_startup_validation:
            executor.gemini.validate_startup()

    @app.get("/")
    def health() -> dict:
        vertex_errors = settings.validate_vertex_settings()
        return {
            "status": "ok" if executor.gemini.is_available else "error",
            "service": "autonomous-research-assistant",
            "vertex_ai_configured": executor.gemini.is_available,
            "gemini_model": settings.gemini_model,
            "vertex_init_error": executor.gemini.init_error,
            "vertex_config_errors": vertex_errors,
            "drive_config_errors": settings.validate_drive_settings(),
            "required_env": {
                "GOOGLE_CLOUD_PROJECT": bool(settings.google_cloud_project),
                "GOOGLE_CLOUD_LOCATION": bool(settings.google_cloud_location),
                "GOOGLE_APPLICATION_CREDENTIALS": bool(settings.google_application_credentials),
            },
            "mcp": mcp_server.health(),
        }

    @app.get("/mcp/health")
    def mcp_health() -> dict:
        return {"status": "ok", **mcp_server.health()}

    app.mount("/outputs", StaticFiles(directory="generated_outputs"), name="outputs")
    app.include_router(generate_router)
    app.include_router(upload_router)
    return app


app = create_app()
