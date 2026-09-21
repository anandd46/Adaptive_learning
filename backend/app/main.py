"""
FastAPI application factory and lifespan manager.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.database import check_db_connection
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.api.router import router
from app.schemas.common import HealthResponse

setup_logging()
settings = get_settings()
logger = get_logger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


# ─── Application Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown events."""
    logger.info(
        "Starting Adaptive Learning Platform",
        extra={"version": settings.app_version, "env": settings.app_env},
    )
    db_ok = check_db_connection()
    if not db_ok:
        logger.error("Database connection failed at startup")
    else:
        logger.info("Database connection verified")

    yield

    logger.info("Shutting down Adaptive Learning Platform")


# ─── App Factory ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Adaptive Learning Platform API",
        description=(
            "Explainable AI-Powered Adaptive Learning Using LLMs and Learning Analytics. "
            "Research-oriented platform for personalized education."
        ),
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ─── Rate Limiting ────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ─── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Exception Handlers ───────────────────────────────────
    register_exception_handlers(app)

    # ─── Routes ───────────────────────────────────────────────
    app.include_router(router)

    # ─── Health Check ─────────────────────────────────────────
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> dict:
        """Health check endpoint — verifies DB connectivity."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": check_db_connection(),
            "environment": settings.app_env,
        }

    logger.info("FastAPI application created successfully")
    return app


app = create_app()
