"""Memory management API endpoints."""

from fastapi import APIRouter, Query
from loguru import logger

from backend.app.agents.memory import list_user_memories
from backend.app.memory.store import delete_memory
from backend.app.memory.vector import delete_memory_embedding

router = APIRouter()


@router.get("/memories")
async def get_memories(
    user_id: str = Query(default="default_user"),
    memory_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> dict:
    """List all memories for a user."""
    logger.info(f"[MemoriesAPI] Listing memories for user={user_id}")
    memories = list_user_memories(user_id=user_id, memory_type=memory_type, limit=limit)
    return {"user_id": user_id, "count": len(memories), "memories": memories}


@router.delete("/memories/{memory_id}")
async def remove_memory(memory_id: str) -> dict:
    """Delete a specific memory by id."""
    logger.info(f"[MemoriesAPI] Deleting memory {memory_id}")
    deleted = delete_memory(memory_id)
    if deleted:
        try:
            delete_memory_embedding(memory_id)
        except Exception as e:
            logger.warning(f"[MemoriesAPI] Failed to delete embedding: {e}")
    return {"deleted": deleted, "memory_id": memory_id}
