"""Executor Agent — sequentially executes plan steps and synthesizes results.

Responsibilities:
- Iterate through plan steps in order
- Call tools via ToolRegistry for "call_tool" steps
- Use LLM for "synthesize" steps to compose final response
- Collect tool logs along the way
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from backend.app.core.llm import call_llm
from backend.app.tools.base import get_registry


async def execute_plan(
    plan: dict[str, Any],
    user_message: str,
    memory_context: str = "",
    user_id: str = "default_user",
) -> dict[str, Any]:
    """Execute a plan and return the response + tool logs.

    Returns dict with keys: response, tool_logs, steps_completed.
    """
    steps = plan.get("steps", [])
    goal = plan.get("goal", user_message)
    reg = get_registry()

    tool_logs: list[dict[str, Any]] = []
    step_results: list[dict[str, Any]] = []

    for step in steps:
        step_id = step.get("id", "?")
        action = step.get("action", "")
        description = step.get("description", "")

        logger.info(f"[Executor] Step {step_id}: {action} — {description}")

        if action == "call_tool":
            tool_name = step.get("tool", "")
            params = step.get("params", {})
            # Inject user_id for tools that need it
            params.setdefault("user_id", user_id)

            tool = reg.get(tool_name)
            if tool is None:
                result = {"status": "error", "error": f"Tool '{tool_name}' not found"}
                logger.warning(f"[Executor] Tool not found: {tool_name}")
            else:
                result = await tool.safe_execute(params)

            tool_log = {
                "step_id": step_id,
                "tool": tool_name,
                "params": params,
                "result": result,
            }
            tool_logs.append(tool_log)
            step_results.append({
                "step_id": step_id,
                "type": "tool_result",
                "tool": tool_name,
                "description": description,
                "data": result,
            })

        elif action == "synthesize":
            # Use LLM to synthesize all collected results into a response
            response = await _synthesize(goal, step_results, memory_context, user_message)
            step_results.append({
                "step_id": step_id,
                "type": "synthesis",
                "description": description,
                "data": response,
            })

        else:
            logger.warning(f"[Executor] Unknown action: {action}")

    # Extract the final synthesis response, or build one if no synthesize step
    response = _extract_final_response(step_results)
    if not response:
        response = await _synthesize(goal, step_results, memory_context, user_message)

    logger.info(f"[Executor] Completed {len(steps)} steps, {len(tool_logs)} tool calls")
    return {
        "response": response,
        "tool_logs": tool_logs,
        "steps_completed": len(steps),
    }


async def _synthesize(
    goal: str,
    step_results: list[dict],
    memory_context: str,
    user_message: str,
) -> str:
    """Use LLM to compose a final response from collected step results."""
    # Format step results for the LLM
    results_text = ""
    for sr in step_results:
        if sr["type"] == "tool_result":
            data = sr.get("data", {})
            results_text += f"\n### {sr['description']}\n"
            result_content = data.get("result", data)
            if isinstance(result_content, (list, dict)):
                results_text += json.dumps(result_content, indent=2, ensure_ascii=False)
            else:
                results_text += str(result_content)
            results_text += "\n"

    system = (
        "You are LifeOS, a personal AI assistant. "
        "Based on the collected data below, compose a helpful, well-structured response "
        "for the user. Reply in the same language as the user."
    )
    if memory_context:
        system += f"\n\nUser context from memory:\n{memory_context}"

    user_content = f"User request: {user_message}\n\nGoal: {goal}\n\nCollected data:\n{results_text}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    try:
        return await call_llm(messages, caller="executor_synthesize")
    except Exception as e:
        logger.error(f"[Executor] Synthesis failed: {e}")
        return f"I gathered the data but had trouble composing a response: {e}"


def _extract_final_response(step_results: list[dict]) -> str:
    """Extract the last synthesis result as the final response."""
    for sr in reversed(step_results):
        if sr["type"] == "synthesis" and sr.get("data"):
            return sr["data"]
    return ""
