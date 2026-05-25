"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.error_handler import setup_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown events."""
    # Startup
    print(f"Starting app in {settings.app_env} mode...")
    # TODO: Initialize APScheduler here (Phase 1 Sprint 2)
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="上海高考复习助手 API",
    description="Shanghai Gaokao Companion - 家长备考陪伴工具后端服务",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Error handlers ────────────────────────────────────────────
setup_error_handlers(app)

# ── Routers (will be registered in Phase 1) ───────────────────
# from app.routers import auth, students, milestones, exams, ...
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0", "env": settings.app_env}


@app.get("/", tags=["system"])
async def root():
    """Root endpoint."""
    return {
        "name": "上海高考复习助手 API",
        "version": "0.1.0",
        "docs": "/docs",
    }
