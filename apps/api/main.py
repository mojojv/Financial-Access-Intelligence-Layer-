"""FastAPI Application Lifecycle, Dependency Injection, and Server Configuration."""
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

from apps.api.routes import router
from src.infrastructure.observability.logging import configure_logging, get_logger
from src.infrastructure.events.event_bus import get_event_bus


logger = get_logger("fail.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup initialization and graceful shutdown.
    """
    # ── Startup ─────────────────────────────────────────────────────────
    env = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level=log_level, env=env)

    logger.info(
        "Financial Access Intelligence Layer starting",
        environment=env,
        log_level=log_level,
        version="0.1.0",
    )

    # Initialize event bus
    bus = get_event_bus()
    app.state.event_bus = bus

    logger.info("Event bus initialized", handlers_registered=0)
    logger.info("FAIL API ready to accept requests")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Financial Access Intelligence Layer shutting down gracefully")
    bus.clear()


def create_app() -> FastAPI:
    """Application factory returning a configured FastAPI instance.

    Returns:
        Fully configured FastAPI application.
    """
    app = FastAPI(
        title="Financial Access Intelligence Layer API",
        description=(
            "Open-source platform measuring financial access via a multi-dimensional "
            "Financial Access Index (FAI), detecting structural barriers, and executing "
            "targeted financial interventions through Interledger Open Payments."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "FAIL Open Source",
            "url": "https://github.com/fail-open/financial-access-intelligence",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )

    # ── CORS ─────────────────────────────────────────────────────────────
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routes ────────────────────────────────────────────────────────
    app.include_router(router)

    # ── Prometheus Metrics Endpoint ───────────────────────────────────────
    @app.get("/metrics", include_in_schema=False, response_class=PlainTextResponse)
    async def prometheus_metrics() -> str:
        """Exposes Prometheus-compatible metrics for scraping."""
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return PlainTextResponse(
                content=generate_latest().decode("utf-8"),
                media_type=CONTENT_TYPE_LATEST,
            )
        except ImportError:
            return PlainTextResponse("# prometheus_client not installed\n", media_type="text/plain")

    # ── Static Dashboard ──────────────────────────────────────────────────
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard() -> FileResponse:
            """Serves the Financial Access Intelligence Console dashboard."""
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app


# Application instance used by uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
