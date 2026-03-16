"""Agent Orchestrator with Intent Router.

LangGraph-based orchestration with intent routing and memory integration.
Receives user input, classifies intent, routes to appropriate agent/handler.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from backend.app.agents.executor import execute_plan
from backend.app.agents.memory import extract_and_save, retrieve_context
from backend.app.agents.planner import generate_plan
from backend.app.core.llm import call_llm


# ---------------------------------------------------------------------------
# Intent definitions
# ---------------------------------------------------------------------------

class IntentType(str, Enum):
    CHAT = "chat"
    PLAN_TASK = "plan_task"
    TOOL_REQUEST = "tool_request"
    MEMORY_WRITE = "memory_write"


class IntentResult(BaseModel):
    intent: IntentType = IntentType.CHAT
    confidence: float = 1.0
    entities: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent state flowing through the graph
# ---------------------------------------------------------------------------

class AgentState(BaseModel):
    """State object passed between LangGraph nodes."""

    # Input
    user_id: str = "default_user"
    session_id: str = "default_session"
    user_message: str = ""

    # Short-term memory: recent conversation turns
    chat_history: list[dict[str, str]] = Field(default_factory=list)

    # Intent routing
    intent: IntentResult = Field(default_factory=IntentResult)

    # Plan (filled by Planner, consumed by Executor)
    plan: dict[str, Any] | None = None

    # Tool execution logs
    tool_logs: list[dict[str, Any]] = Field(default_factory=list)

    # Memory context retrieved for this turn
    memory_context: str = ""

    # Final response
    response: str = ""

    # Debug trace
    trace: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Intent Router — LLM-based classification
# ---------------------------------------------------------------------------

INTENT_SYSTEM_PROMPT = """\
You are an intent classifier for LifeOS, a personal AI assistant.
Classify the user message into exactly ONE of these intents:

1. "chat" — casual conversation, greetings, general questions, opinions
2. "plan_task" — user wants to plan, schedule, organize tasks or work
3. "tool_request" — user wants to search info, check calendar, manage todos
4. "memory_write" — user explicitly asks you to remember something about them

Respond in JSON only:
{"intent": "<intent>", "confidence": <0-1>, "entities": {<optional extracted params>}}

Examples:
- "hello" → {"intent": "chat", "confidence": 0.95, "entities": {}}
- "帮我规划明天的工作" → {"intent": "plan_task", "confidence": 0.9, "entities": {"timeframe": "tomorrow"}}
- "搜一下最新的AI新闻" → {"intent": "tool_request", "confidence": 0.9, "entities": {"tool": "search", "query": "latest AI news"}}
- "记住我喜欢晚上学习" → {"intent": "memory_write", "confidence": 0.95, "entities": {"content": "用户喜欢晚上学习"}}
"""



async def classify_intent(state: dict) -> dict:
    """LangGraph node: classify user intent via LLM."""
    user_message = state["user_message"]
    logger.info(f"[IntentRouter] Classifying: {user_message[:80]}")

    messages = [
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await call_llm(messages)
        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        parsed = json.loads(raw)
        intent = IntentResult(
            intent=IntentType(parsed.get("intent", "chat")),
            confidence=parsed.get("confidence", 0.8),
            entities=parsed.get("entities", {}),
        )
    except Exception as e:
        logger.warning(f"[IntentRouter] Failed to parse intent, defaulting to chat: {e}")
        intent = IntentResult(intent=IntentType.CHAT, confidence=0.5)

    logger.info(f"[IntentRouter] Result: {intent.intent.value} (conf={intent.confidence})")
    return {
        "intent": intent.model_dump(),
        "trace": state.get("trace", []) + [f"intent_router → {intent.intent.value}"],
    }


# ---------------------------------------------------------------------------
# Handler nodes
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = (
    "You are LifeOS, a proactive personal AI assistant. "
    "You help the user manage tasks, plans, and daily life. "
    "Be helpful, concise, and friendly. Reply in the same language as the user."
)


async def handle_chat(state: dict) -> dict:
    """LangGraph node: handle plain chat via LLM."""
    logger.info("[ChatHandler] Generating response")

    # Build messages with history
    messages: list[dict[str, str]] = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for turn in state.get("chat_history", [])[-10:]:
        messages.append(turn)
    messages.append({"role": "user", "content": state["user_message"]})

    # Add memory context if available
    memory_ctx = state.get("memory_context", "")
    if memory_ctx:
        messages[0]["content"] += f"\n\nRelevant user context:\n{memory_ctx}"

    try:
        reply = await call_llm(messages)
    except Exception as e:
        logger.error(f"[ChatHandler] LLM error: {e}")
        reply = f"Sorry, I encountered an error: {e}"

    return {
        "response": reply,
        "trace": state.get("trace", []) + ["handle_chat → done"],
    }


async def handle_plan_task(state: dict) -> dict:
    """LangGraph node: generate a plan via Planner, then execute via Executor."""
    logger.info("[PlanTaskHandler] Generating plan and executing")
    user_message = state["user_message"]
    memory_context = state.get("memory_context", "")
    entities = state.get("intent", {}).get("entities", {})
    user_id = state.get("user_id", "default_user")

    # Step 1: Planner generates the plan
    plan = await generate_plan(
        user_message=user_message,
        memory_context=memory_context,
        entities=entities,
    )

    # Step 2: Executor runs the plan
    exec_result = await execute_plan(
        plan=plan,
        user_message=user_message,
        memory_context=memory_context,
        user_id=user_id,
    )

    return {
        "response": exec_result["response"],
        "plan": plan,
        "tool_logs": exec_result.get("tool_logs", []),
        "trace": state.get("trace", []) + [
            f"planner → {len(plan.get('steps', []))} steps",
            f"executor → {exec_result.get('steps_completed', 0)} completed",
        ],
    }


async def handle_tool_request(state: dict) -> dict:
    """LangGraph node: direct tool request — plan and execute in one shot."""
    logger.info("[ToolRequestHandler] Generating plan for tool request")
    user_message = state["user_message"]
    memory_context = state.get("memory_context", "")
    entities = state.get("intent", {}).get("entities", {})
    user_id = state.get("user_id", "default_user")

    # Use Planner + Executor same as plan_task
    plan = await generate_plan(
        user_message=user_message,
        memory_context=memory_context,
        entities=entities,
    )

    exec_result = await execute_plan(
        plan=plan,
        user_message=user_message,
        memory_context=memory_context,
        user_id=user_id,
    )

    return {
        "response": exec_result["response"],
        "plan": plan,
        "tool_logs": exec_result.get("tool_logs", []),
        "trace": state.get("trace", []) + [
            f"planner → {len(plan.get('steps', []))} steps",
            f"executor → {exec_result.get('steps_completed', 0)} completed",
        ],
    }


async def handle_memory_write(state: dict) -> dict:
    """LangGraph node: extract and persist user memory via Memory Agent."""
    logger.info("[MemoryWriteHandler] Extracting and saving memory")
    user_id = state.get("user_id", "default_user")

    result = await extract_and_save(
        user_id=user_id,
        user_message=state["user_message"],
    )

    if result:
        reply = f"Got it! I'll remember: \"{result['summary'] or result['content']}\""
    else:
        reply = "I noted your message, but didn't find specific information to remember long-term."

    return {
        "response": reply,
        "trace": state.get("trace", []) + [
            f"handle_memory_write → {'saved' if result else 'skipped'}"
        ],
    }


# ---------------------------------------------------------------------------
# Memory context loading (runs before intent handling)
# ---------------------------------------------------------------------------

async def load_memory_context(state: dict) -> dict:
    """LangGraph node: retrieve relevant memories and inject as context."""
    user_id = state.get("user_id", "default_user")
    user_message = state.get("user_message", "")

    try:
        context = await retrieve_context(user_id=user_id, query=user_message, top_k=5)
    except Exception as e:
        logger.warning(f"[MemoryContext] Retrieval failed: {e}")
        context = ""

    if context:
        logger.info(f"[MemoryContext] Loaded {context.count(chr(10)) + 1} memory items")

    return {
        "memory_context": context,
        "trace": state.get("trace", []) + [
            f"load_memory → {len(context)} chars" if context else "load_memory → empty"
        ],
    }


# ---------------------------------------------------------------------------
# Post-turn memory extraction (runs after response generation)
# ---------------------------------------------------------------------------

async def post_turn_extract(state: dict) -> dict:
    """LangGraph node: extract memories from user message after responding.

    Only runs for non-memory_write intents (memory_write already handles saving).
    """
    intent_type = state.get("intent", {}).get("intent", "chat")
    if intent_type == "memory_write":
        return {"trace": state.get("trace", []) + ["post_extract → skipped (already saved)"]}

    user_id = state.get("user_id", "default_user")
    result = await extract_and_save(
        user_id=user_id,
        user_message=state["user_message"],
    )

    return {
        "trace": state.get("trace", []) + [
            f"post_extract → {'saved' if result else 'nothing'}"
        ],
    }


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

def route_by_intent(state: dict) -> str:
    """Conditional edge: route to handler based on classified intent."""
    intent_data = state.get("intent", {})
    intent_type = intent_data.get("intent", "chat")
    return intent_type


# ---------------------------------------------------------------------------
# Build the LangGraph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the orchestrator state graph.

    Flow:
      classify_intent → load_memory_context → route_by_intent
        → handle_chat / handle_plan_task / handle_tool_request / handle_memory_write
        → post_turn_extract → END
    """
    graph = StateGraph(dict)

    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("load_memory_context", load_memory_context)
    graph.add_node("handle_chat", handle_chat)
    graph.add_node("handle_plan_task", handle_plan_task)
    graph.add_node("handle_tool_request", handle_tool_request)
    graph.add_node("handle_memory_write", handle_memory_write)
    graph.add_node("post_turn_extract", post_turn_extract)

    # Entry → intent classification → memory loading → routing
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "load_memory_context")

    # Conditional routing from memory context to handlers
    graph.add_conditional_edges(
        "load_memory_context",
        route_by_intent,
        {
            "chat": "handle_chat",
            "plan_task": "handle_plan_task",
            "tool_request": "handle_tool_request",
            "memory_write": "handle_memory_write",
        },
    )

    # All handlers → post-turn memory extraction → END
    graph.add_edge("handle_chat", "post_turn_extract")
    graph.add_edge("handle_plan_task", "post_turn_extract")
    graph.add_edge("handle_tool_request", "post_turn_extract")
    graph.add_edge("handle_memory_write", "post_turn_extract")
    graph.add_edge("post_turn_extract", END)

    return graph.compile()


# Compiled graph singleton
orchestrator_graph = build_graph()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_orchestrator(
    user_id: str,
    session_id: str,
    message: str,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Run the orchestrator graph and return the final state."""
    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": message,
        "chat_history": chat_history or [],
        "intent": {},
        "plan": None,
        "tool_logs": [],
        "memory_context": "",
        "response": "",
        "trace": [],
    }

    logger.info(f"[Orchestrator] Running for user={user_id}, session={session_id}")
    result = await orchestrator_graph.ainvoke(initial_state)
    logger.info(f"[Orchestrator] Trace: {result.get('trace', [])}")
    return result
