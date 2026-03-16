"""Proactive messages API — fetch and manage system-initiated messages."""

from fastapi import APIRouter, Query
from loguru import logger

from backend.app.agents.proactive import (
    get_proactive_messages,
    mark_read,
    trigger_briefing,
)

router = APIRouter()


@router.get("/proactive/messages")
async def list_messages(
    user_id: str = Query(default="default_user"),
    limit: int = Query(default=10, le=50),
) -> dict:
    """Get recent proactive messages for a user."""
    messages = get_proactive_messages(user_id=user_id, limit=limit)
    return {"user_id": user_id, "count": len(messages), "messages": messages}


@router.post("/proactive/trigger")
async def manual_trigger(user_id: str = Query(default="default_user")) -> dict:
    """Manually trigger a morning briefing (for demo/testing)."""
    logger.info(f"[ProactiveAPI] Manual trigger for user={user_id}")
    return await trigger_briefing(user_id)


@router.post("/proactive/messages/{message_id}/read")
async def read_message(message_id: str, user_id: str = Query(default="default_user")) -> dict:
    """Mark a proactive message as read."""
    success = mark_read(user_id, message_id)
    return {"marked": success, "message_id": message_id}
