"""Planner Agent — decomposes user tasks into executable step-by-step plans.

Input: task description, user context, memory, available tools
Output: structured Plan with goal, required tools, and ordered steps
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from backend.app.core.llm import call_llm
from backend.app.tools.base import get_registry

# ---------------------------------------------------------------------------
# Plan schema
# ---------------------------------------------------------------------------

PLAN_EXAMPLE = {
    "goal": "规划明天工作",
    "required_tools": ["calendar", "todo"],
    "steps": [
        {"id": 1, "action": "call_tool", "tool": "calendar", "params": {"day": "tomorrow"}, "description": "读取明天日程"},
        {"id": 2, "action": "call_tool", "tool": "todo", "params": {"action": "list"}, "description": "读取未完成待办"},
        {"id": 3, "action": "synthesize", "description": "按紧急程度排序，生成时间块计划"},
    ],
}

# ---------------------------------------------------------------------------
# Planner prompt
# ---------------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """\
You are a task planner for LifeOS, a personal AI assistant.

Given a user request, break it down into an executable plan.

Available tools:
{tools_desc}

Each step must be one of:
- "call_tool": invoke a tool with params
- "synthesize": use LLM to analyze/summarize collected results

Output JSON only:
{{
  "goal": "<what the user wants>",
  "required_tools": ["tool_name", ...],
  "steps": [
    {{"id": 1, "action": "call_tool", "tool": "<name>", "params": {{...}}, "description": "<what this step does>"}},
    {{"id": 2, "action": "synthesize", "description": "<what to summarize>"}}
  ]
}}

Rules:
- Keep plans simple: 2-5 steps max for MVP
- Only use tools that are available
- The final step should typically be "synthesize" to compose the answer
- Reply in the same language as the user request
"""


async def generate_plan(
    user_message: str,
    memory_context: str = "",
    entities: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an execution plan from a user request.

    Returns the plan dict with goal, required_tools, and steps.
    """
    reg = get_registry()
    tools_desc = json.dumps(reg.list_tools(), indent=2, ensure_ascii=False)

    system = PLANNER_SYSTEM_PROMPT.format(tools_desc=tools_desc)
    if memory_context:
        system += f"\n\nUser context from memory:\n{memory_context}"

    user_content = user_message
    if entities:
        user_content += f"\n\nExtracted entities: {json.dumps(entities, ensure_ascii=False)}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = await call_llm(messages, caller="planner")
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        plan = json.loads(raw)
        logger.info(
            f"[Planner] Generated plan: goal={plan.get('goal', '?')}, "
            f"steps={len(plan.get('steps', []))}"
        )
        return plan
    except Exception as e:
        logger.error(f"[Planner] Failed to generate plan: {e}")
        # Fallback: simple synthesize-only plan
        return {
            "goal": user_message,
            "required_tools": [],
            "steps": [
                {"id": 1, "action": "synthesize", "description": f"Directly answer: {user_message}"}
            ],
        }
