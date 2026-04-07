"""Semantic search module for the RAG pipeline.

Delegates to `app.rag.embeddings.search_resumes` (FAISS-backed).
"""

from __future__ import annotations

import logging

from app.rag.embeddings import search_resumes

logger = logging.getLogger(__name__)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Search for candidates matching a query.

    Args:
        query: Search query (typically the job description).
        top_k: Number of top results to return.

    Returns:
        List of candidate dicts with relevance scores.
    """
    logger.info(f"Running semantic_search for query (first 50 chars): {query[:50]}...")
    return search_resumes(query, k=top_k)

