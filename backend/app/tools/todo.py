"""Todo Tool — manage tasks via SQLite storage."""

from __future__ import annotations

import json
import uuid
from typing import Any

from backend.app.memory.store import get_connection
from backend.app.tools.base import BaseTool


class TodoTool(BaseTool):
    name = "todo"
    description = (
        "Manage user tasks/todos. Supports actions: "
        "'list' (view tasks), 'add' (create task), 'update' (change status/priority), "
        "'delete' (remove task)."
    )
    input_schema = {
        "action": {
            "type": "string",
            "enum": ["list", "add", "update", "delete"],
            "description": "The action to perform",
        },
        "title": {"type": "string", "description": "Task title (for add)"},
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent"],
            "description": "Task priority (for add/update)",
        },
        "status": {
            "type": "string",
            "enum": ["pending", "in_progress", "done"],
            "description": "Task status (for update)",
        },
        "task_id": {"type": "string", "description": "Task ID (for update/delete)"},
        "user_id": {"type": "string", "description": "User ID", "default": "default_user"},
    }

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "list")
        user_id = params.get("user_id", "default_user")

        if action == "list":
            return self._list_tasks(user_id)
        elif action == "add":
            return self._add_task(user_id, params)
        elif action == "update":
            return self._update_task(params)
        elif action == "delete":
            return self._delete_task(params)
        else:
            return {"result": f"Unknown action: {action}"}

    def _list_tasks(self, user_id: str) -> dict[str, Any]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY "
                "CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
                "WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC",
                (user_id,),
            ).fetchall()
        finally:
            conn.close()

        tasks = [dict(r) for r in rows]
        return {"result": tasks, "count": len(tasks)}

    def _add_task(self, user_id: str, params: dict) -> dict[str, Any]:
        title = params.get("title", "")
        if not title:
            return {"result": "Title is required to add a task."}

        task_id = str(uuid.uuid4())
        priority = params.get("priority", "medium")

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO tasks (id, user_id, title, priority, source) VALUES (?, ?, ?, ?, ?)",
                (task_id, user_id, title, priority, "agent"),
            )
            conn.commit()
        finally:
            conn.close()

        return {"result": f"Task added: {title}", "task_id": task_id, "title": title}

    def _update_task(self, params: dict) -> dict[str, Any]:
        task_id = params.get("task_id", "")
        if not task_id:
            return {"result": "task_id is required for update."}

        updates: dict[str, Any] = {}
        if "status" in params:
            updates["status"] = params["status"]
        if "priority" in params:
            updates["priority"] = params["priority"]
        if "title" in params and params.get("action") == "update":
            updates["title"] = params["title"]

        if not updates:
            return {"result": "No fields to update."}

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]

        conn = get_connection()
        try:
            cur = conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()

        if cur.rowcount == 0:
            return {"result": f"Task {task_id} not found."}
        return {"result": f"Task {task_id} updated.", "updates": updates}

    def _delete_task(self, params: dict) -> dict[str, Any]:
        task_id = params.get("task_id", "")
        if not task_id:
            return {"result": "task_id is required for delete."}

        conn = get_connection()
        try:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        finally:
            conn.close()

        if cur.rowcount == 0:
            return {"result": f"Task {task_id} not found."}
        return {"result": f"Task {task_id} deleted."}
