"""Base tool interface and tool registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class BaseTool(ABC):
    """Abstract base class for all LifeOS tools."""

    name: str
    description: str
    input_schema: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool with given parameters.

        Returns a dict with at least a "result" key.
        """

    async def safe_execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute with error handling, always returns a dict."""
        try:
            result = await self.execute(params)
            logger.info(f"[Tool:{self.name}] Success")
            return {"status": "success", **result}
        except Exception as e:
            logger.error(f"[Tool:{self.name}] Error: {e}")
            return {"status": "error", "error": str(e)}


class ToolRegistry:
    """Registry of available tools, keyed by name."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.debug(f"[ToolRegistry] Registered: {tool.name}")

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        """Return tool descriptions for LLM planning."""
        return [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in self._tools.values()
        ]

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())


# Global registry singleton
registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry, registering built-in tools on first call."""
    if not registry.names:
        _register_defaults()
    return registry


def _register_defaults() -> None:
    """Register all built-in tools."""
    from backend.app.tools.calendar import CalendarTool
    from backend.app.tools.search import SearchTool
    from backend.app.tools.todo import TodoTool

    registry.register(SearchTool())
    registry.register(CalendarTool())
    registry.register(TodoTool())
