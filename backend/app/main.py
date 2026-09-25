"""
Main FastAPI Application Entry Point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, check


def create_app() -> FastAPI:
    """Application factory for the ScamCheck FastAPI backend."""
    app = FastAPI(
        title="ScamCheck Backend API",
        description="Detection and risk assessment API for suspicious text messages.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Allowed origins for local development (React Vite dev server, etc.)
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include route modules
    app.include_router(health.router)
    app.include_router(check.router)

    return app


app = create_app()
