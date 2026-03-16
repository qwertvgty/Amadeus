"""LifeOS Backend - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.api.chat import router as chat_router
from backend.app.core.logger import setup_logger
from backend.app.memory.store import ensure_db_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logger()
    logger.info("LifeOS backend starting...")
    ensure_db_exists()
    yield
    logger.info("LifeOS backend shutting down...")


app = FastAPI(
    title="LifeOS API",
    description="Personal AI Agent System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
