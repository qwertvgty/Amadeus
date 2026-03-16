"""Core Pydantic schemas for LifeOS."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# === API Request/Response ===


class ChatRequest(BaseModel):
    user_id: str = "default_user"
    session_id: str = "default_session"
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None
    plan: dict[str, Any] | None = None
    tool_logs: list[dict[str, Any]] = []


# === Database Models ===


class UserProfile(BaseModel):
    user_id: str
    name: str = ""
    role: str = ""
    preferences_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Memory(BaseModel):
    id: str
    user_id: str
    memory_type: str  # "profile" | "episodic"
    tags: str = "[]"  # JSON array string
    content: str
    summary: str = ""
    source_turn_id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Task(BaseModel):
    id: str
    user_id: str
    title: str
    status: str = "pending"  # pending / in_progress / done
    priority: str = "medium"  # low / medium / high / urgent
    due_time: datetime | None = None
    source: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    session_id: str
    user_id: str
    latest_context: str = ""
    current_goal: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class ToolLog(BaseModel):
    id: str
    session_id: str
    tool_name: str
    input_payload: str = "{}"
    output_payload: str = "{}"
    status: str = "success"
    created_at: datetime = Field(default_factory=datetime.now)
