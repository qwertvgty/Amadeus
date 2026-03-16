"""SQLite storage operations for memories, user profiles, and sessions."""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger

DB_PATH = Path("data/lifeos.db")


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_exists() -> None:
    """Create the database if it doesn't exist, and run migrations."""
    if not DB_PATH.exists():
        logger.warning("Database not found, initializing...")
        from scripts.init_db import init_database

        init_database()
    else:
        # Ensure new tables exist (idempotent migration)
        _migrate()


def _migrate() -> None:
    """Add any missing tables to an existing database."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trace_logs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                intent TEXT DEFAULT '',
                plan_json TEXT DEFAULT '{}',
                tool_logs_json TEXT DEFAULT '[]',
                trace_json TEXT DEFAULT '[]',
                response TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Memory CRUD
# ---------------------------------------------------------------------------

def save_memory(
    user_id: str,
    content: str,
    memory_type: str = "episodic",
    tags: list[str] | None = None,
    summary: str = "",
    source_turn_id: str = "",
) -> str:
    """Write a memory record to SQLite. Returns the memory id."""
    memory_id = str(uuid.uuid4())
    tags_json = json.dumps(tags or [], ensure_ascii=False)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO memories (id, user_id, memory_type, tags, content, summary, source_turn_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, user_id, memory_type, tags_json, content, summary, source_turn_id),
        )
        conn.commit()
        logger.info(f"[MemoryStore] Saved memory {memory_id} type={memory_type} for user={user_id}")
    finally:
        conn.close()
    return memory_id


def get_memories(
    user_id: str,
    memory_type: str | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """Retrieve memories with optional type/tag filtering, newest first."""
    query = "SELECT * FROM memories WHERE user_id = ?"
    params: list = [user_id]

    if memory_type:
        query += " AND memory_type = ?"
        params.append(memory_type)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    results = [dict(r) for r in rows]

    # Client-side tag filtering (tags stored as JSON array string)
    if tags:
        tag_set = set(tags)
        results = [
            r for r in results
            if tag_set & set(json.loads(r.get("tags", "[]")))
        ]

    return results


def delete_memory(memory_id: str) -> bool:
    """Delete a memory by id. Returns True if deleted."""
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

def get_user_profile(user_id: str) -> dict | None:
    """Retrieve a user profile."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def update_user_profile(user_id: str, **fields) -> None:
    """Update user profile fields (name, role, preferences_json)."""
    allowed = {"name", "role", "preferences_json"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return

    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]

    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE user_profiles SET {set_clause} WHERE user_id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Session short-term context (for future DB-backed history)
# ---------------------------------------------------------------------------

def upsert_session(session_id: str, user_id: str, context: str = "", goal: str = "") -> None:
    """Create or update a session record."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO sessions (session_id, user_id, latest_context, current_goal)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                   latest_context = excluded.latest_context,
                   current_goal = excluded.current_goal""",
            (session_id, user_id, context, goal),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Trace logs (observability)
# ---------------------------------------------------------------------------

def save_trace_log(
    session_id: str,
    user_id: str,
    user_message: str,
    intent: str = "",
    plan: dict | None = None,
    tool_logs: list | None = None,
    trace: list | None = None,
    response: str = "",
    duration_ms: int = 0,
) -> str:
    """Persist a full request trace for debugging."""
    trace_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO trace_logs
               (id, session_id, user_id, user_message, intent, plan_json, tool_logs_json, trace_json, response, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace_id,
                session_id,
                user_id,
                user_message,
                intent,
                json.dumps(plan or {}, ensure_ascii=False),
                json.dumps(tool_logs or [], ensure_ascii=False),
                json.dumps(trace or [], ensure_ascii=False),
                response,
                duration_ms,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return trace_id


def get_trace_logs(session_id: str, limit: int = 50) -> list[dict]:
    """Retrieve trace logs for a session, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM trace_logs WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    finally:
        conn.close()

    results = []
    for r in rows:
        d = dict(r)
        # Parse JSON fields back
        for field in ("plan_json", "tool_logs_json", "trace_json"):
            try:
                d[field] = json.loads(d.get(field, "{}"))
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


def get_recent_traces(user_id: str, limit: int = 20) -> list[dict]:
    """Retrieve recent trace logs across all sessions for a user."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM trace_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    results = []
    for r in rows:
        d = dict(r)
        for field in ("plan_json", "tool_logs_json", "trace_json"):
            try:
                d[field] = json.loads(d.get(field, "{}"))
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results
