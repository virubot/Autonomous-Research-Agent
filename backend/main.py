from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.executor import AgentExecutor
from backend.routes.generate import router as generate_router
from backend.routes.upload import router as upload_router
from backend.utils.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    executor = AgentExecutor(settings=settings)

    app = FastAPI(
        title="Autonomous Research Assistant API",
        version="2.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.executor = executor

    @app.get("/")
    def health() -> dict:
        return {
            "status": "ok",
            "service": "autonomous-research-assistant",
            "vertex_ai_configured": executor.gemini.is_available,
            "gemini_model": settings.gemini_model,
            "vertex_init_error": executor.gemini.init_error,
            "vertex_config_errors": settings.validate_vertex_settings(),
            "drive_config_errors": settings.validate_drive_settings(),
        }

    app.include_router(generate_router)
    app.include_router(upload_router)
    return app


app = create_app()
