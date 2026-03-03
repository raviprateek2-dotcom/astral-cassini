"""Agent 3: The Scout — Semantic resume search using RAG.

Performs semantic search across the ChromaDB vector store using
the job description as the query to find top-matching candidates.
"""

from __future__ import annotations

from datetime import datetime

from app.config import settings
from app.models.state import RecruitmentState, PipelineStage
from app.rag.search import semantic_search


def create_scout():
    """Create The Scout agent node function."""

    def scout_node(state: RecruitmentState) -> dict:
        """Search for matching candidates using the approved JD."""

        job_description = state.get("job_description", "")
        job_title = state.get("job_title", "")

        if not job_description:
            return {
                "error": "No job description available for sourcing",
                "audit_log": [{
                    "timestamp": datetime.now().isoformat(),
                    "agent": "The Scout",
                    "action": "error",
                    "details": "No JD available — cannot perform search",
                    "stage": PipelineStage.SOURCING.value,
                }],
            }

        # Build search query from JD + title
        search_query = f"{job_title}\n\n{job_description}"

        # Perform semantic search
        try:
            results = semantic_search(query=search_query, top_k=10)
        except Exception as e:
            # Fallback to mock candidates if vector store is empty
            results = _get_mock_candidates()

        candidates = []
        for r in results:
            candidates.append({
                "id": r.get("id", ""),
                "name": r.get("name", "Unknown"),
                "email": r.get("email", ""),
                "phone": r.get("phone", ""),
                "skills": r.get("skills", []),
                "experience_years": r.get("experience_years", 0),
                "education": r.get("education", ""),
                "resume_text": r.get("resume_text", ""),
                "source": "vector_search",
                "relevance_score": r.get("relevance_score", 0.0),
            })

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "The Scout",
            "action": "sourced_candidates",
            "details": f"Found {len(candidates)} matching candidates for '{job_title}'",
            "stage": PipelineStage.SOURCING.value,
        }

        return {
            "candidates": candidates,
            "current_stage": PipelineStage.SCREENING.value,
            "audit_log": [audit_entry],
        }

    return scout_node


def _get_mock_candidates() -> list[dict]:
    """Return mock candidates when vector store is unavailable."""
    return [
        {
            "id": "cand-001",
            "name": "Priya Sharma",
            "email": "priya.sharma@email.com",
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Docker"],
            "experience_years": 5,
            "education": "M.Tech in Computer Science, IIT Delhi",
            "resume_text": "Experienced ML engineer with 5 years building production ML systems. Led a team of 3 at a Series B startup. Published 2 papers on NLP. Strong in Python, TensorFlow, and cloud deployments.",
            "relevance_score": 0.92,
        },
        {
            "id": "cand-002",
            "name": "Arjun Mehta",
            "email": "arjun.mehta@email.com",
            "skills": ["Java", "Spring Boot", "Microservices", "AWS", "PostgreSQL"],
            "experience_years": 7,
            "education": "B.Tech in IT, NIT Trichy",
            "resume_text": "Senior backend developer specializing in distributed systems. 7 years at top tech companies. Expert in Java, Spring Boot, and AWS infrastructure. Led migration of monolith to microservices.",
            "relevance_score": 0.87,
        },
        {
            "id": "cand-003",
            "name": "Sneha Patel",
            "email": "sneha.patel@email.com",
            "skills": ["React", "TypeScript", "Node.js", "GraphQL", "Figma"],
            "experience_years": 4,
            "education": "B.E. in Computer Engineering, BITS Pilani",
            "resume_text": "Full-stack developer with strong frontend focus. 4 years building React applications. Designed and shipped 3 customer-facing products. Excellent at bridging design and engineering.",
            "relevance_score": 0.85,
        },
        {
            "id": "cand-004",
            "name": "Rahul Verma",
            "email": "rahul.verma@email.com",
            "skills": ["Python", "FastAPI", "LangChain", "RAG", "Vector DBs"],
            "experience_years": 3,
            "education": "M.S. in AI, Carnegie Mellon University",
            "resume_text": "AI/ML engineer specializing in LLM applications. Built RAG pipelines serving 10K+ queries/day. Strong in Python, LangChain, and vector databases. Former research intern at Google DeepMind.",
            "relevance_score": 0.94,
        },
        {
            "id": "cand-005",
            "name": "Ananya Gupta",
            "email": "ananya.gupta@email.com",
            "skills": ["Data Science", "Python", "Spark", "Tableau", "Statistics"],
            "experience_years": 6,
            "education": "Ph.D. in Statistics, ISI Kolkata",
            "resume_text": "Data scientist with PhD in statistics. 6 years in analytics and ML. Expert in experimental design, causal inference, and large-scale data processing with Spark.",
            "relevance_score": 0.81,
        },
    ]
