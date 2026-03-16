"""Chat API endpoint — routes through the Orchestrator with trace logging."""

import time

from fastapi import APIRouter
from loguru import logger

from backend.app.agents.orchestrator import run_orchestrator
from backend.app.memory.store import save_trace_log
from backend.app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

# In-memory short-term chat history per session
_session_history: dict[str, list[dict[str, str]]] = {}

MAX_HISTORY_TURNS = 20


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle a chat message through the Orchestrator pipeline."""
    logger.info(f"Chat request from user={request.user_id}: {request.message[:100]}")
    start = time.monotonic()

    # Retrieve session history
    history = _session_history.setdefault(request.session_id, [])

    # Run orchestrator
    result = await run_orchestrator(
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
        chat_history=history,
    )

    duration_ms = int((time.monotonic() - start) * 1000)

    reply = result.get("response", "Sorry, something went wrong.")
    intent_data = result.get("intent", {})
    intent_type = intent_data.get("intent", "chat")
    trace = result.get("trace", [])
    plan = result.get("plan")
    tool_logs = result.get("tool_logs", [])

    # Persist trace log to DB
    trace_id = ""
    try:
        trace_id = save_trace_log(
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.message,
            intent=intent_type,
            plan=plan,
            tool_logs=tool_logs,
            trace=trace,
            response=reply,
            duration_ms=duration_ms,
        )
    except Exception as e:
        logger.warning(f"Failed to save trace log: {e}")

    # Update session history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": reply})
    if len(history) > MAX_HISTORY_TURNS * 2:
        history[:] = history[-(MAX_HISTORY_TURNS * 2):]

    return ChatResponse(
        reply=reply,
        intent=intent_type,
        plan=plan,
        tool_logs=tool_logs,
        trace=trace,
        trace_id=trace_id,
        duration_ms=duration_ms,
    )
