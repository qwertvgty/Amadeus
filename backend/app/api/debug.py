"""Debug/observability API — view traces, tool logs, and system state."""

from fastapi import APIRouter, Query
from loguru import logger

from backend.app.memory.store import get_recent_traces, get_trace_logs
from backend.app.tools.base import get_registry

router = APIRouter()


@router.get("/debug/session/{session_id}")
async def get_session_traces(session_id: str, limit: int = Query(default=50, le=200)) -> dict:
    """Get all trace logs for a specific session."""
    traces = get_trace_logs(session_id=session_id, limit=limit)
    return {"session_id": session_id, "count": len(traces), "traces": traces}


@router.get("/debug/traces")
async def get_user_traces(
    user_id: str = Query(default="default_user"),
    limit: int = Query(default=20, le=100),
) -> dict:
    """Get recent traces across all sessions for a user."""
    traces = get_recent_traces(user_id=user_id, limit=limit)
    return {"user_id": user_id, "count": len(traces), "traces": traces}


@router.get("/debug/tools")
async def list_tools() -> dict:
    """List all registered tools and their schemas."""
    reg = get_registry()
    return {"tools": reg.list_tools()}


@router.get("/debug/system")
async def system_info() -> dict:
    """Return system status overview."""
    from backend.app.core.config import settings
    from backend.app.memory.store import get_connection

    conn = get_connection()
    try:
        memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        trace_count = conn.execute("SELECT COUNT(*) FROM trace_logs").fetchone()[0]
        user_count = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]
    finally:
        conn.close()

    reg = get_registry()

    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "tools": reg.names,
        "counts": {
            "users": user_count,
            "memories": memory_count,
            "tasks": task_count,
            "traces": trace_count,
        },
    }
