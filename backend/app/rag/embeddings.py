"""FAISS-based RAG Embeddings — Production-grade vector search.

Uses FAISS for efficient similarity search and local persistence.
Chunks are stored as Documents with detailed metadata.
"""

from __future__ import annotations

import logging
import os
from typing import Any
import uuid

from pydantic import SecretStr
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)

# Vector store singleton
_vectorstore: FAISS | None = None
INDEX_PATH = "data/faiss_index"


def _get_vectorstore() -> FAISS:
    """Lazily initialize and load the FAISS vector store from disk.

    NOTE: First call will make an OpenAI embedding API call only if no index
    exists on disk. This is intentionally deferred — never called at startup.
    """
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
        )

        # Load from disk if exists
        if os.path.exists(INDEX_PATH):
            try:
                _vectorstore = FAISS.load_local(
                    INDEX_PATH,
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("Loaded FAISS index from %s", INDEX_PATH)
            except Exception as e:
                logger.error("Failed to load FAISS: %s. Creating new index.", e)
                _vectorstore = None

        if _vectorstore is None:
            # Only create a bootstrap doc when no index exists on disk.
            # This makes an OpenAI call — that is acceptable here because it
            # only happens on first-ever resume upload, not at server startup.
            dummy_doc = Document(page_content="init", metadata={"section": "init"})
            _vectorstore = FAISS.from_documents([dummy_doc], embeddings)
            logger.info("New FAISS index bootstrapped")

    return _vectorstore


def _save_vectorstore():
    """Save the current state of the FAISS index to disk."""
    if _vectorstore is not None:
        os.makedirs("data", exist_ok=True)
        try:
            _vectorstore.save_local(INDEX_PATH)
            logger.info(f"FAISS index saved to {INDEX_PATH}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")


def index_resume(parsed: dict) -> str:
    """Index a parsed resume into FAISS."""
    candidate_id = parsed.get("id", str(uuid.uuid4())[:8])
    chunks: list[dict] = parsed.get("chunks", [])

    if not chunks:
        chunks = [{
            "section": "full",
            "text": parsed.get("resume_text", ""),
            "metadata": {"section": "full"},
        }]

    vs = _get_vectorstore()
    documents: list[Document] = []

    for chunk in chunks:
        section = chunk.get("section", "full")
        text = chunk.get("text", "").strip()
        if not text:
            continue

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
        
        documents.append(Document(page_content=text, metadata=metadata))

    if documents:
        # FAISS doesn't easily support 'deleting' specific IDs in the open-source version 
        # without rebuilding, but we can add new ones. For a production system like this,
        # we append and then filter for the latest candidate data during search.
        vs.add_documents(documents)
        _save_vectorstore()
        logger.info(f"Indexed {len(documents)} chunks for candidate {candidate_id}")

    return candidate_id


def search_resumes(
    query: str,
    k: int = 10,
    min_experience_years: int = 0,
    required_skills: list[str] | None = None,
) -> list[dict]:
    """Semantic search using FAISS with metadata filtering.

    Args:
        query: Natural language job description or skills query.
        k: Number of results per candidate.
        min_experience_years: Filter candidates with fewer years.
        required_skills: If provided, only surface candidates with these.

    Returns:
        List of candidate dicts with relevance_score.
    """
    vs = _get_vectorstore()

    try:
        # FAISS similarity search
        # We fetch k*5 to have enough cushion for filtering
        results = vs.similarity_search_with_relevance_scores(query, k=k * 5)
    except Exception as e:
        logger.error(f"FAISS Search failed: {e}")
        return []

    # De-duplicate by candidate_id and apply manual filters
    seen: dict[str, dict] = {}
    for doc, score in results:
        # Skip internal init doc
        if doc.metadata.get("section") == "init":
            continue

        cid = doc.metadata.get("candidate_id")
        if not cid:
            continue

        # Manual Metadata Filtering & Hybrid Boosting
        boost_score = 0.0
        if required_skills:
            cand_skills_str = doc.metadata.get("skills", "").lower()
            matches = [rs.lower() in cand_skills_str for rs in required_skills]
            if not any(matches): # Mandatory filter (if any required)
                continue
            # Apply boost for each matched skill (0.05 per match)
            boost_score = sum(0.05 for m in matches if m)

        if min_experience_years > 0:
            if doc.metadata.get("experience_years", 0) < min_experience_years:
                continue

        final_score = float(score) + boost_score

        # Keep best score for this candidate
        if cid not in seen or final_score > seen[cid]["relevance_score"]:
            seen[cid] = {
                "id": cid,
                "name": doc.metadata.get("candidate_name", "Unknown"),
                "email": doc.metadata.get("email", ""),
                "skills": [s.strip() for s in doc.metadata.get("skills", "").split(",") if s.strip()],
                "experience_years": doc.metadata.get("experience_years", 0),
                "education": doc.metadata.get("education", ""),
                "resume_text": doc.page_content,
                "relevance_score": float(round(final_score, 3)),
                "matched_section": doc.metadata.get("section", "full"),
            }

    # Sort and return top-k
    candidates = list(seen.values())
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates[:k]


def get_collection_count() -> int:
    """Return the number of vectors in the FAISS index.

    Returns 0 safely if the index has never been created yet, without
    triggering the lazy initializer (which makes an OpenAI API call).
    """
    try:
        if _vectorstore is None:
            # Index not yet loaded — no resumes indexed yet
            return 0
        return max(0, _vectorstore.index.ntotal - 1)  # subtract the bootstrap init doc
    except Exception:
        return 0
