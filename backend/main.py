"""LifeOS Backend - FastAPI Application."""

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.api.chat import router as chat_router
from backend.app.api.debug import router as debug_router
from backend.app.api.memories import router as memories_router
from backend.app.api.proactive import router as proactive_router
from backend.app.core.logger import setup_logger
from backend.app.memory.store import ensure_db_exists

# ---------------------------------------------------------------------------
# APScheduler setup
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler()


def _setup_scheduler() -> None:
    """Register scheduled jobs."""
    from backend.app.agents.proactive import scheduled_morning_briefing

    # Daily morning briefing at 08:00
    scheduler.add_job(
        scheduled_morning_briefing,
        trigger=CronTrigger(hour=8, minute=0),
        id="morning_briefing",
        name="Daily morning briefing",
        replace_existing=True,
    )
    logger.info("[Scheduler] Morning briefing job registered (daily at 08:00)")


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logger()
    logger.info("LifeOS backend starting...")
    ensure_db_exists()

    # Start scheduler
    _setup_scheduler()
    scheduler.start()
    logger.info("[Scheduler] Started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("LifeOS backend shutting down...")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LifeOS API",
    description="Personal AI Agent System",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(chat_router, prefix="/api")
app.include_router(memories_router, prefix="/api")
app.include_router(proactive_router, prefix="/api")
app.include_router(debug_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
