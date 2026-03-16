"""Chroma vector store for semantic memory retrieval."""

from __future__ import annotations

from datetime import datetime, timezone

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from backend.app.core.config import settings

# ---------------------------------------------------------------------------
# Singleton Chroma client & collection
# ---------------------------------------------------------------------------

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "lifeos_memories"


def _get_collection() -> chromadb.Collection:
    """Lazy-init the Chroma persistent client and collection."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"[VectorStore] Collection '{COLLECTION_NAME}' ready, "
            f"count={_collection.count()}"
        )
    return _collection


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_memory_embedding(
    memory_id: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    """Add a memory's text to the vector store.

    Chroma will auto-generate the embedding using its default model.
    """
    col = _get_collection()
    meta = metadata or {}
    meta["indexed_at"] = datetime.now(timezone.utc).isoformat()

    col.upsert(
        ids=[memory_id],
        documents=[content],
        metadatas=[meta],
    )
    logger.debug(f"[VectorStore] Upserted embedding for memory {memory_id}")


def search_memories(
    query: str,
    user_id: str | None = None,
    n_results: int = 5,
) -> list[dict]:
    """Semantic search over memory embeddings.

    Returns list of dicts with keys: id, content, score, metadata.
    """
    col = _get_collection()
    if col.count() == 0:
        return []

    where_filter = {"user_id": user_id} if user_id else None

    results = col.query(
        query_texts=[query],
        n_results=min(n_results, col.count()),
        where=where_filter,
    )

    hits: list[dict] = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for i, mid in enumerate(ids):
        hits.append({
            "id": mid,
            "content": docs[i] if i < len(docs) else "",
            "score": 1 - distances[i] if i < len(distances) else 0,  # cosine distance → similarity
            "metadata": metadatas[i] if i < len(metadatas) else {},
        })

    return hits


def delete_memory_embedding(memory_id: str) -> None:
    """Remove a memory embedding from the vector store."""
    col = _get_collection()
    col.delete(ids=[memory_id])
    logger.debug(f"[VectorStore] Deleted embedding for memory {memory_id}")
