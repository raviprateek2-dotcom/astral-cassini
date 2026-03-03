"""In-Memory embeddings — section-level chunking for finer retrieval.

Improvement over v1:
- Stores each resume section (Skills, Experience, Education) as a separate chunk
- Uses InMemoryVectorStore due to Python 3.14/Pydantic V1 incompatibility with Chroma DB
"""

from __future__ import annotations

import logging
from typing import Any
import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from app.config import settings

logger = logging.getLogger(__name__)

import os
import pickle

_vectorstore: InMemoryVectorStore | None = None
PERSIST_PATH = "data/vectorstore.pkl"


def _get_vectorstore() -> InMemoryVectorStore:
    """Lazily initialise and load the InMemory vector store from disk."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        _vectorstore = InMemoryVectorStore(embedding=embeddings)
        
        # Load from disk if exists
        if os.path.exists(PERSIST_PATH):
            try:
                with open(PERSIST_PATH, "rb") as f:
                    data = pickle.load(f)
                    _vectorstore.store = data
                logger.info(f"Loaded {len(data)} documents from {PERSIST_PATH}")
            except Exception as e:
                logger.error(f"Failed to load vectorstore: {e}")
        else:
            logger.info("New InMemoryVectorStore initialised")
            
    return _vectorstore


def _save_vectorstore():
    """Save the current state of the vector store to disk."""
    if _vectorstore is not None:
        os.makedirs("data", exist_ok=True)
        try:
            with open(PERSIST_PATH, "wb") as f:
                pickle.dump(_vectorstore.store, f)
            logger.info(f"Vectorstore saved to {PERSIST_PATH}")
        except Exception as e:
            logger.error(f"Failed to save vectorstore: {e}")


def index_resume(parsed: dict) -> str:
    # ... existing index logic ...
    # (Abbreviated for multi_replace_file_content clarity - assume logic remains but calls _save_vectorstore at the end)
    # I will replace the whole function in the actual call to avoid "..." errors
    candidate_id = parsed.get("id", "unknown")
    chunks: list[dict] = parsed.get("chunks", [])

    if not chunks:
        chunks = [{
            "section": "full",
            "text": parsed.get("resume_text", ""),
            "metadata": {"section": "full"},
        }]

    vs = _get_vectorstore()
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for chunk in chunks:
        section = chunk.get("section", "full")
        text = chunk.get("text", "").strip()
        if not text: continue

        doc_id = f"{candidate_id}_{section}"
        metadata: dict[str, Any] = {
            "candidate_id": candidate_id,
            "candidate_name": parsed.get("name", "Unknown"),
            "email": parsed.get("email", ""),
            "section": section,
            "skills": ", ".join(parsed.get("skills", [])),
            "experience_years": parsed.get("experience_years", 0),
            "education": parsed.get("education", "")[:200],
            "source_file": parsed.get("source_file", ""),
        }
        metadata.update(chunk.get("metadata", {}))
        texts.append(text)
        metadatas.append(metadata)
        ids.append(doc_id)

    if texts:
        try:
            existing_ids = [d for d in ids if d in vs.store]
            if existing_ids: vs.delete(existing_ids)
        except Exception: pass
        vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        _save_vectorstore() # NEW: Persist after indexing
        logger.info(f"Indexed and Persisted {len(texts)} chunks for candidate {candidate_id}")

    return candidate_id


def search_resumes(
    query: str,
    k: int = 10,
    min_experience_years: int = 0,
    required_skills: list[str] | None = None,
) -> list[dict]:
    """Semantic search with optional pre-filtering.

    Args:
        query: Natural language job description or skills query.
        k: Number of results.
        min_experience_years: Filter candidates with fewer years.
        required_skills: If provided, only surface candidates with any of these.

    Returns:
        List of candidate dicts with relevance_score.
    """
    vs = _get_vectorstore()

    # InMemory filter dict format
    def filter_func(doc) -> bool:
        if min_experience_years > 0:
            if doc.metadata.get("experience_years", 0) < min_experience_years:
                return False
        return True

    try:
        # InMemoryVectorStore supports similarity_search_with_relevance_scores roughly
        results = vs.similarity_search_with_relevance_scores(
            query, k=k * 3, filter=filter_func
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

    # De-duplicate by candidate_id (take best score per candidate)
    seen: dict[str, dict] = {}
    for doc, score in results:
        cid = doc.metadata.get("candidate_id", doc.id)
        if cid not in seen or score > seen[cid]["relevance_score"]:
            seen[cid] = {
                "id": cid,
                "name": doc.metadata.get("candidate_name", "Unknown"),
                "email": doc.metadata.get("email", ""),
                "skills": [s.strip() for s in doc.metadata.get("skills", "").split(",") if s.strip()],
                "experience_years": doc.metadata.get("experience_years", 0),
                "education": doc.metadata.get("education", ""),
                "resume_text": doc.page_content,
                "relevance_score": float(round(float(score), 3)),
                "matched_section": doc.metadata.get("section", "full"),
            }

    # Optional skill post-filter
    candidates = list(seen.values())
    if required_skills is not None:
        lower_skills = [s.lower() for s in required_skills]
        candidates = [
            c for c in candidates
            if any(
                rs in " ".join(c.get("skills", [])).lower()
                for rs in lower_skills
            )
        ]

    # Sort by relevance descending, return top-k
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates[:k]


def get_collection_count() -> int:
    """Return the number of documents indexed."""
    try:
        vs = _get_vectorstore()
        return len(vs.store)
    except Exception:
        return 0

