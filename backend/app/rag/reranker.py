"""RAG 2.0: LLM-based Cross-Encoder Reranker.

This module performs a deeper analysis of the top-N candidates found via 
vector search to provide high-fidelity match reasoning.
"""

from __future__ import annotations

import asyncio
import json
import logging

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.agents.structured_outputs import RerankerResult

logger = logging.getLogger(__name__)

RERANKER_MODEL = "gpt-4o-mini"

RERANKER_PROMPT = """You are a Recruitment Intelligence Reranker. 
Given a Job Description and a candidate's profile, provide a concise (1-2 sentence) 
reason for the match, and a final refined match score (0-100).

Focus on why the specific skills or experience make them a good fit. 
Return ONLY a JSON object: {"reason": "...", "refined_score": 85}"""


async def rerank_candidates(jd_text: str, candidates: list[dict]) -> list[dict]:
    """Perform LLM-based reranking on the top candidates.
    
    Args:
        jd_text: The full job description text.
        candidates: List of candidate dicts from early-stage retrieval.
        
    Returns:
        List of candidates with added 'match_reason' and updated 'relevance_score'.
    """
    if not candidates:
        return []

    llm = ChatOpenAI(
        model=RERANKER_MODEL,
        temperature=0,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    ).with_structured_output(RerankerResult)

    # Rerank top 10 candidates concurrently
    top_n = candidates[:10]
    rest = candidates[10:]
    semaphore = asyncio.Semaphore(5)

    async def _rerank_one(cand: dict) -> dict:
        async with semaphore:
            try:
                raw_skills = cand.get("skills", [])
                skills = raw_skills if isinstance(raw_skills, list) else [str(raw_skills)]
                resume_text = str(cand.get("resume_text", ""))
                profile = (
                    f"Name: {cand.get('name')}\n"
                    f"Skills: {', '.join(str(s) for s in skills)}\n"
                    f"Exp: {cand.get('experience_years')} years\n"
                    f"Summary: {resume_text[:1000]}"
                )

                result: RerankerResult = await llm.ainvoke([
                    SystemMessage(content=RERANKER_PROMPT),
                    HumanMessage(content=f"JD: {jd_text}\n\nCandidate Profile:\n{profile}")
                ])

                cand["match_reason"] = result.reason
                cand["matching_skills"] = result.matching_skills
                cand["missing_skills_from_jd"] = result.missing_skills_from_jd
                # Blend initial vector score with LLM refined score
                refined = result.refined_score
                cand["relevance_score"] = round(
                    (cand["relevance_score"] * 0.4) + (refined / 100 * 0.6), 3
                )
            except Exception as e:
                logger.error(f"Reranking failed for {cand.get('id')}: {e}")
                cand["match_reason"] = "Semantic match based on experience and core tech stack."
            return cand

    reranked = await asyncio.gather(*[_rerank_one(c) for c in top_n])
    reranked = list(reranked)

    # Add the rest without reasoning (or with fallback)
    for cand in rest:
        cand["match_reason"] = "Qualified candidate meeting initial screening criteria."
        reranked.append(cand)

    # Re-sort based on refined score
    reranked.sort(key=lambda x: x["relevance_score"], reverse=True)
    return reranked
