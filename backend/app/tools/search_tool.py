"""Search tool wrapper for The Scout (Agent 3).

Provides a LangChain-compatible tool interface for semantic search.
"""

from __future__ import annotations

from app.rag.search import semantic_search


def search_resumes(query: str, top_k: int = 10) -> list[dict]:
    """Search the resume vector store.

    Args:
        query: Search query (typically the job description).
        top_k: Number of top results to return.

    Returns:
        List of matching candidate profiles.
    """
    return semantic_search(query=query, top_k=top_k)
