"""Calendar Tool (mock) — returns simulated schedule data for demo."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from backend.app.tools.base import BaseTool

# Mock calendar data for demo purposes
MOCK_EVENTS = [
    {
        "title": "Team standup",
        "start": "09:00",
        "end": "09:30",
        "type": "meeting",
    },
    {
        "title": "Code review session",
        "start": "10:00",
        "end": "11:00",
        "type": "meeting",
    },
    {
        "title": "Lunch break",
        "start": "12:00",
        "end": "13:00",
        "type": "break",
    },
    {
        "title": "Project planning",
        "start": "14:00",
        "end": "15:00",
        "type": "meeting",
    },
    {
        "title": "Deep work / coding",
        "start": "15:00",
        "end": "17:30",
        "type": "focus",
    },
]


class CalendarTool(BaseTool):
    name = "calendar"
    description = "Get calendar events/schedule for today or tomorrow (mock data for demo)."
    input_schema = {
        "day": {
            "type": "string",
            "description": "Which day: 'today' or 'tomorrow'",
            "default": "today",
        },
    }

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        day = params.get("day", "today").lower()

        if day == "tomorrow":
            target = datetime.now() + timedelta(days=1)
        else:
            target = datetime.now()

        date_str = target.strftime("%Y-%m-%d")

        return {
            "result": MOCK_EVENTS,
            "date": date_str,
            "day": day,
            "event_count": len(MOCK_EVENTS),
        }
