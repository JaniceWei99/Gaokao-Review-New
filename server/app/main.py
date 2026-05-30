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
    print(f"Starting app in {settings.app_env} mode...")
    if settings.app_env in ("development", "dev", "production"):
        from app.jobs.scheduler import start_scheduler, stop_scheduler

        start_scheduler()
    yield
    if settings.app_env in ("development", "dev", "production"):
        from app.jobs.scheduler import stop_scheduler

        stop_scheduler()
    from app.services.cache_service import close_redis
    await close_redis()
    print("Shutting down...")


app = FastAPI(
    title="高考家长帮 API",
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

# ── Routers ───────────────────────────────────────────────────
from app.routers import auth, action_cards, ai_chat, ai_features, dashboard, error_notes, exams, growth_records, knowledge, milestones, quotes, school_progress, students, subjects, subscription, upload

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(subjects.router, prefix="/api/subjects", tags=["subjects"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["quotes"])
app.include_router(milestones.router, prefix="/api/students/{student_id}/milestones", tags=["milestones"])
app.include_router(action_cards.router, prefix="/api/students/{student_id}/action-cards", tags=["action-cards"])
app.include_router(dashboard.router, prefix="/api/students/{student_id}/dashboard", tags=["dashboard"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(exams.router, prefix="/api/students/{student_id}/exams", tags=["exams"])
app.include_router(error_notes.router, prefix="/api/students/{student_id}/error-notes", tags=["error-notes"])
app.include_router(growth_records.router, prefix="/api/students/{student_id}/growth-records", tags=["growth-records"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["subscription"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(school_progress.router, prefix="/api/students/{student_id}/school-progress", tags=["school-progress"])
app.include_router(ai_chat.router, prefix="/api/students/{student_id}/ai-chat", tags=["ai-chat"])
app.include_router(ai_features.router, prefix="/api/students/{student_id}/ai", tags=["ai-features"])


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0", "env": settings.app_env}


@app.get("/", tags=["system"])
async def root():
    """Root endpoint."""
    return {
        "name": "高考家长帮 API",
        "version": "0.1.0",
        "docs": "/docs",
    }
