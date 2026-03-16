"""Proactive Agent — generates time-triggered suggestions and reminders.

MVP: daily morning briefing based on todos and calendar.
Stores generated messages for frontend polling.
"""

from __future__ import annotations

import json
import uuid
from collections import deque
from datetime import datetime

from loguru import logger

from backend.app.core.llm import call_llm
from backend.app.memory.store import get_connection, get_memories
from backend.app.tools.calendar import CalendarTool
from backend.app.tools.todo import TodoTool

# ---------------------------------------------------------------------------
# In-memory message queue per user (lightweight for MVP)
# ---------------------------------------------------------------------------

_message_queues: dict[str, deque] = {}
MAX_QUEUE_SIZE = 50


def _get_queue(user_id: str) -> deque:
    if user_id not in _message_queues:
        _message_queues[user_id] = deque(maxlen=MAX_QUEUE_SIZE)
    return _message_queues[user_id]


def get_proactive_messages(user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent proactive messages for a user."""
    q = _get_queue(user_id)
    items = list(q)[-limit:]
    return items


def push_message(user_id: str, content: str, msg_type: str = "morning_briefing") -> dict:
    """Push a proactive message to the user's queue."""
    msg = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": msg_type,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "read": False,
    }
    _get_queue(user_id).append(msg)
    logger.info(f"[Proactive] Pushed {msg_type} for user={user_id}")
    return msg


def mark_read(user_id: str, message_id: str) -> bool:
    """Mark a proactive message as read."""
    for msg in _get_queue(user_id):
        if msg["id"] == message_id:
            msg["read"] = True
            return True
    return False


# ---------------------------------------------------------------------------
# Morning briefing generation
# ---------------------------------------------------------------------------

BRIEFING_SYSTEM_PROMPT = """\
You are LifeOS, a personal AI assistant generating a daily morning briefing.
Based on the user's schedule and pending tasks, create a concise, friendly briefing.

Include:
1. Today's schedule overview (key events and times)
2. Pending tasks summary, sorted by priority
3. One actionable suggestion for the day

Keep it brief (under 200 words). Use the same language as the user context.
If user memories suggest a language preference, use that language.
Default to Chinese (中文) for the briefing.
"""


async def generate_morning_briefing(user_id: str = "default_user") -> str:
    """Generate a morning briefing by reading calendar + todos + memories."""
    logger.info(f"[Proactive] Generating morning briefing for user={user_id}")

    # Gather data
    calendar_tool = CalendarTool()
    todo_tool = TodoTool()

    cal_result = await calendar_tool.safe_execute({"day": "today"})
    todo_result = await todo_tool.safe_execute({"action": "list", "user_id": user_id})

    # Get user memories for personalization
    memories = get_memories(user_id=user_id, limit=5)
    memory_text = "\n".join(f"- {m['content']}" for m in memories) if memories else "No memories yet."

    # Build context
    events = cal_result.get("result", [])
    events_text = json.dumps(events, indent=2, ensure_ascii=False) if events else "No events today."

    tasks = todo_result.get("result", [])
    if isinstance(tasks, list):
        pending = [t for t in tasks if t.get("status") != "done"]
        tasks_text = "\n".join(
            f"- [{t.get('priority', 'medium')}] {t.get('title', '?')}" for t in pending
        ) if pending else "No pending tasks."
    else:
        tasks_text = "No pending tasks."

    user_content = (
        f"Date: {datetime.now().strftime('%Y-%m-%d %A')}\n\n"
        f"Today's schedule:\n{events_text}\n\n"
        f"Pending tasks:\n{tasks_text}\n\n"
        f"User memories:\n{memory_text}"
    )

    messages = [
        {"role": "system", "content": BRIEFING_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        briefing = await call_llm(messages)
    except Exception as e:
        logger.error(f"[Proactive] Briefing generation failed: {e}")
        briefing = f"Good morning! I couldn't generate your briefing today: {e}"

    # Push to queue
    push_message(user_id, briefing, msg_type="morning_briefing")
    return briefing


# ---------------------------------------------------------------------------
# Scheduler job (called by APScheduler)
# ---------------------------------------------------------------------------

async def scheduled_morning_briefing() -> None:
    """APScheduler job: generate morning briefing for all known users."""
    logger.info("[Proactive] Running scheduled morning briefing")

    # Get all user IDs from DB
    conn = get_connection()
    try:
        rows = conn.execute("SELECT user_id FROM user_profiles").fetchall()
    finally:
        conn.close()

    for row in rows:
        try:
            await generate_morning_briefing(row["user_id"])
        except Exception as e:
            logger.error(f"[Proactive] Failed for user {row['user_id']}: {e}")


# ---------------------------------------------------------------------------
# Manual trigger (for testing / demo)
# ---------------------------------------------------------------------------

async def trigger_briefing(user_id: str = "default_user") -> dict:
    """Manually trigger a briefing (for demo/testing via API)."""
    content = await generate_morning_briefing(user_id)
    return {"user_id": user_id, "briefing": content}
