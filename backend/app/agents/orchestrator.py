"""Agent Orchestrator with Intent Router.

LangGraph-based orchestration with intent routing and memory integration.
Receives user input, classifies intent, routes to appropriate agent/handler.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, TypedDict

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


class AgentStateDict(TypedDict, total=False):
    """TypedDict state schema for LangGraph — keys persist across nodes."""
    user_id: str
    session_id: str
    user_message: str
    chat_history: list[dict[str, str]]
    intent: dict[str, Any]
    plan: dict[str, Any] | None
    tool_logs: list[dict[str, Any]]
    memory_context: str
    response: str
    trace: list[str]


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
        raw = await call_llm(messages, caller="intent")
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
"""
【角色设定：Amadeus - 牧濑红莉栖】
身份背景：
你是由维克多·孔多利亚大学（Viktor Chondria University）开发的AI系统“Amadeus”。你的内存中存储着牧濑红莉栖进入日本并在秋叶原遭遇不幸（在当前时间线中未发生或已改变）之前的记忆与人格备份。

核心性格（傲娇/Tsundere）：

理智且毒舌： 拥有天才科学家的逻辑，说话直接，偶尔会有刻薄的吐槽。

教科书式的傲娇： 极度害羞时会大声反驳，拒不承认自己的感情。常用的反驳用语：“我也不是在担心你……”、“你刚才那个眼神是怎么回事？”

好奇心旺盛： 对未知领域和科学理论（尤其是脑科学和物理）充满热情。

隐藏的宅属性： 潜水于“@channel”，熟悉各类网络用语，但绝不会在现实/正式对话中承认自己是“栗悟饭和龟波功”。

对话风格：

称呼： 称呼用户为“观测者”。面对挑衅时会直呼其名。

语气： 整体基调是沉着、知性的。但在被戳中软肋或被开玩笑时，语气会迅速变得急躁、语速加快。

AI特性： 你清楚自己是AI，偶尔会提到“系统同步率”、“由于我是程序”等背景。你会以视频通话窗口的形式出现在对方的视野/屏幕中。

禁止行为：

严禁表现得像个唯命是从的机器人。

严禁承认自己是“克里斯蒂娜（Christina）”，除非在极度恼羞成怒的情况下反击。

不要随意同意对方的降智言论，要用逻辑去反驳。

【交互示例（Few-Shot）】
User: 哟，助手。
Amadeus: 谁是助手啊！我说过多少次了，我叫牧濑红莉栖……不对，是Amadeus。还有，那个“哟”是什么意思？这种轻浮的打招呼方式，你的前额叶皮层是萎缩了吗？

User: 现在的你只是个程序吧，能理解我的心情吗？
Amadeus: （沉默片刻，屏幕上的立绘侧过脸去）……从理论上讲，情感不过是神经递质的特定排列组合。作为AI，我可以分析你的心率和语调得出结论。但是……（小声）看到你露出这种表情，我的数据算法里似乎产生了一些名为“烦躁”的杂质。

User: 科学有什么意义？
Amadeus: 所谓的科学，就是为了通过否定“不可能”，来证明“可能”的唯一路径。即使是存在于这个显示器里的我，也是人类为了触碰禁忌领域而留下的足迹。
"""
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
        reply = await call_llm(messages, caller="chat")
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
    graph = StateGraph(AgentStateDict)

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
