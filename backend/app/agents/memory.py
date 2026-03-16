"""Memory Agent — extracts, stores, and retrieves user memories.

Responsibilities:
- Extract memory-worthy information from user messages (via LLM)
- Write memories to SQLite + Chroma
- Retrieve relevant memories via hybrid search (structured + semantic)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from loguru import logger

from backend.app.core.llm import call_llm
from backend.app.memory.store import get_memories, save_memory
from backend.app.memory.vector import (
    add_memory_embedding,
    delete_memory_embedding,
    search_memories,
)

# ---------------------------------------------------------------------------
# Memory extraction prompt
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """\
You are a memory extraction module for LifeOS, a personal AI assistant.

Analyze the user message and decide whether it contains information worth remembering long-term.

Rules:
- Only extract if the message contains: personal preferences, goals, habits, identity info, \
important events, or explicit "remember this" requests.
- Do NOT extract greetings, casual chat, or transient questions.
- Classify as "profile" (identity/preferences/habits) or "episodic" (events/goals/states).
- Assign relevant tags from: ["preference", "goal", "habit", "identity", "emotion", "event"].
- Write a concise summary (one sentence).

Respond in JSON only:
{
  "should_save": true/false,
  "memory_type": "profile" | "episodic",
  "tags": ["tag1", "tag2"],
  "content": "<the key information to remember>",
  "summary": "<one-sentence summary>"
}

If nothing worth saving, return: {"should_save": false}
"""


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

async def extract_and_save(user_id: str, user_message: str, turn_id: str = "") -> dict | None:
    """Extract memory from a user message and persist it.

    Returns the saved memory dict, or None if nothing worth saving.
    """
    messages = [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await call_llm(messages, caller="memory_extract")
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        parsed = json.loads(raw)
    except Exception as e:
        logger.warning(f"[MemoryAgent] Extraction failed: {e}")
        return None

    if not parsed.get("should_save", False):
        logger.debug("[MemoryAgent] Nothing worth saving")
        return None

    content = parsed.get("content", user_message)
    memory_type = parsed.get("memory_type", "episodic")
    tags = parsed.get("tags", [])
    summary = parsed.get("summary", "")

    # Save to SQLite
    memory_id = save_memory(
        user_id=user_id,
        content=content,
        memory_type=memory_type,
        tags=tags,
        summary=summary,
        source_turn_id=turn_id,
    )

    # Save embedding to Chroma
    add_memory_embedding(
        memory_id=memory_id,
        content=content,
        metadata={
            "user_id": user_id,
            "memory_type": memory_type,
            "tags": json.dumps(tags),
            "summary": summary,
        },
    )

    logger.info(f"[MemoryAgent] Saved: type={memory_type} tags={tags} → {summary}")
    return {
        "id": memory_id,
        "memory_type": memory_type,
        "tags": tags,
        "content": content,
        "summary": summary,
    }


async def retrieve_context(user_id: str, query: str, top_k: int = 5) -> str:
    """Retrieve relevant memories and format them as context string.

    Uses hybrid retrieval:
    1. Semantic search via Chroma
    2. Recency boost from structured store
    3. Score = semantic_score * 0.5 + recency * 0.5
    """
    # Semantic search
    semantic_hits = search_memories(query=query, user_id=user_id, n_results=top_k * 2)

    # Structured retrieval (recent memories)
    recent_memories = get_memories(user_id=user_id, limit=top_k * 2)
    recent_by_id = {m["id"]: m for m in recent_memories}

    # Merge and score
    now = datetime.now(timezone.utc)
    scored: list[tuple[float, dict]] = []

    for hit in semantic_hits:
        mid = hit["id"]
        semantic_score = hit.get("score", 0)

        # Recency score: 1.0 for now, decays over days
        recency = 0.5  # default if not found in structured store
        if mid in recent_by_id:
            created = recent_by_id[mid].get("created_at", "")
            try:
                dt = datetime.fromisoformat(created)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = (now - dt).total_seconds() / 86400
                recency = max(0, 1.0 - age_days / 30)  # linear decay over 30 days
            except (ValueError, TypeError):
                pass

        final_score = semantic_score * 0.5 + recency * 0.5
        scored.append((final_score, {
            "id": mid,
            "content": hit.get("content", ""),
            "score": round(final_score, 3),
        }))

    # Add recent memories not in semantic hits
    seen_ids = {h["id"] for h in semantic_hits}
    for mem in recent_memories:
        if mem["id"] not in seen_ids:
            scored.append((0.3, {  # low score for non-semantic matches
                "id": mem["id"],
                "content": mem.get("content", ""),
                "score": 0.3,
            }))

    # Sort by score descending, take top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return ""

    lines = [f"- {item['content']}" for _, item in top]
    context = "\n".join(lines)
    logger.debug(f"[MemoryAgent] Retrieved {len(top)} memories for context")
    return context


def list_user_memories(user_id: str, memory_type: str | None = None, limit: int = 50) -> list[dict]:
    """List all memories for a user (for API/debug)."""
    return get_memories(user_id=user_id, memory_type=memory_type, limit=limit)
