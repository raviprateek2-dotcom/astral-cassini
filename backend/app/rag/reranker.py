"""RAG 2.0: LLM-based Cross-Encoder Reranker.

This module performs a deeper analysis of the top-N candidates found via 
vector search to provide high-fidelity match reasoning.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings

logger = logging.getLogger(__name__)

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
        model=settings.llm_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )

    reranked = []
    # Rerank only top 3 to keep it fast and cost-effective
    top_n = candidates[:3]
    rest = candidates[3:]

    for cand in top_n:
        try:
            profile = f"Name: {cand.get('name')}\nSkills: {', '.join(cand.get('skills', []))}\nExp: {cand.get('experience_years')} years\nSummary: {cand.get('resume_text')[:1000]}"
            
            res = await llm.ainvoke([
                SystemMessage(content=RERANKER_PROMPT),
                HumanMessage(content=f"JD: {jd_text}\n\nCandidate Profile:\n{profile}")
            ])
            
            content = res.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            cand["match_reason"] = data.get("reason", "Highly relevant profile matching core requirements.")
            # Blend initial vector score with LLM refined score
            # Vector score is usually 0.7-0.9, refined is 0-100
            refined = data.get("refined_score", 80)
            cand["relevance_score"] = round((cand["relevance_score"] * 0.4) + (refined / 100 * 0.6), 3)
            
        except Exception as e:
            logger.error(f"Reranking failed for {cand.get('id')}: {e}")
            cand["match_reason"] = "Semantic match based on experience and core tech stack."
        
        reranked.append(cand)

    # Add the rest without reasoning (or with fallback)
    for cand in rest:
        cand["match_reason"] = "Qualified candidate meeting initial screening criteria."
        reranked.append(cand)

    # Re-sort based on refined score
    reranked.sort(key=lambda x: x["relevance_score"], reverse=True)
    return reranked
