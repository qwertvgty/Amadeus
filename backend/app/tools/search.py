"""Search Tool — uses LLM knowledge as a search proxy for MVP.

In production, this would call a real search API (Tavily, SerpAPI, etc.).
For MVP, we use the LLM's knowledge to simulate search results.
"""

from __future__ import annotations

from typing import Any

from backend.app.core.llm import call_llm
from backend.app.tools.base import BaseTool


class SearchTool(BaseTool):
    name = "search"
    description = "Search for information on a topic. Returns a summary of findings."
    input_schema = {
        "query": {"type": "string", "description": "The search query"},
    }

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        query = params.get("query", "")
        if not query:
            return {"result": "No query provided."}

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a search engine assistant. Given a query, provide a concise, "
                    "factual summary of the most relevant information. Include key points "
                    "in bullet form. Reply in the same language as the query. "
                    "If you're not sure about something, say so."
                ),
            },
            {"role": "user", "content": f"Search: {query}"},
        ]

        reply = await call_llm(messages, caller="tool_search")
        return {"result": reply, "query": query, "source": "llm_knowledge"}
