"""Skill synonym dictionary and matching utilities.

Used by the Screener (Agent 4) and Scout (Agent 3) to improve keyword
matching accuracy.  Handles common aliases, abbreviations, and variant
spellings so that "Postgres" matches "PostgreSQL", "React.js" matches
"React", etc.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Canonical synonym map
# Keys are canonical (lowercase) skill names.
# Values are sets of known aliases (also lowercase).
# ---------------------------------------------------------------------------

SKILL_SYNONYMS: dict[str, set[str]] = {
    # Databases
    "postgresql": {"postgres", "psql", "pg", "postgre"},
    "mongodb": {"mongo"},
    "mysql": {"mariadb"},
    "dynamodb": {"dynamo"},
    "elasticsearch": {"elastic", "es", "opensearch"},
    "microsoft sql server": {"mssql", "sql server", "tsql", "t-sql"},
    "redis": {"redis cache"},
    "cassandra": {"apache cassandra"},
    # Languages
    "javascript": {"js", "ecmascript", "es6", "es2015"},
    "typescript": {"ts"},
    "python": {"py", "python3", "cpython"},
    "c++": {"cpp", "c plus plus"},
    "c#": {"csharp", "c sharp", "dotnet", ".net"},
    "golang": {"go"},
    "rust": {"rustlang"},
    "ruby": {"rb"},
    "kotlin": {"kt"},
    "swift": {"swiftlang"},
    # Frontend
    "react": {"react.js", "reactjs", "react js"},
    "next.js": {"nextjs", "next"},
    "vue": {"vue.js", "vuejs", "vue js"},
    "angular": {"angularjs", "angular.js"},
    "svelte": {"sveltekit"},
    "tailwindcss": {"tailwind", "tailwind css"},
    # Backend
    "node.js": {"node", "nodejs", "node js"},
    "express": {"express.js", "expressjs"},
    "fastapi": {"fast api"},
    "django": {"django rest framework", "drf"},
    "flask": {"flask api"},
    "spring boot": {"spring", "spring framework", "springboot"},
    "ruby on rails": {"rails", "ror"},
    # Cloud & DevOps
    "aws": {"amazon web services", "amazon aws"},
    "gcp": {"google cloud", "google cloud platform"},
    "azure": {"microsoft azure", "ms azure"},
    "kubernetes": {"k8s", "kube"},
    "docker": {"docker compose", "dockerfile", "containerization"},
    "terraform": {"hashicorp terraform", "iac"},
    "ci/cd": {"cicd", "ci cd", "continuous integration", "continuous deployment"},
    "jenkins": {"jenkins ci"},
    "github actions": {"gh actions", "gha"},
    "ansible": {"ansible playbook"},
    # Data & ML
    "machine learning": {"ml"},
    "deep learning": {"dl"},
    "artificial intelligence": {"ai"},
    "natural language processing": {"nlp"},
    "computer vision": {"cv"},
    "tensorflow": {"tf", "tensor flow"},
    "pytorch": {"torch"},
    "scikit-learn": {"scikit", "sklearn", "sci-kit learn"},
    "pandas": {"pd"},
    "numpy": {"np"},
    "apache spark": {"spark", "pyspark"},
    "apache kafka": {"kafka"},
    "apache airflow": {"airflow"},
    # LLM / AI Eng
    "langchain": {"lang chain"},
    "langgraph": {"lang graph"},
    "rag": {"retrieval augmented generation"},
    "vector database": {"vector db", "vectordb", "vector store"},
    "chromadb": {"chroma"},
    "pinecone": {"pinecone db"},
    "faiss": {"facebook ai similarity search"},
    # Tools & Practices
    "git": {"github", "gitlab", "bitbucket", "version control"},
    "agile": {"scrum", "kanban", "agile methodology"},
    "jira": {"atlassian jira"},
    "graphql": {"graph ql", "gql"},
    "rest api": {"restful", "rest", "restful api"},
    "microservices": {"micro services", "microservice architecture"},
    "sql": {"structured query language"},
    "linux": {"unix", "ubuntu", "centos", "debian"},
    "figma": {"figma design"},
    "tableau": {"tableau desktop"},
}


# ---------------------------------------------------------------------------
# Reverse lookup cache (built once on import)
# Maps every alias → its canonical name
# ---------------------------------------------------------------------------

_ALIAS_TO_CANONICAL: dict[str, str] = {}


def _build_reverse_map() -> None:
    """Populate the alias→canonical reverse lookup."""
    for canonical, aliases in SKILL_SYNONYMS.items():
        _ALIAS_TO_CANONICAL[canonical] = canonical
        for alias in aliases:
            _ALIAS_TO_CANONICAL[alias] = canonical


_build_reverse_map()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_skill(skill: str) -> str:
    """Return the canonical name for a skill, or the lowercased input if unknown.

    >>> normalize_skill("React.js")
    'react'
    >>> normalize_skill("PostgreSQL")
    'postgresql'
    >>> normalize_skill("Some Unknown Skill")
    'some unknown skill'
    """
    lowered = skill.strip().lower()
    return _ALIAS_TO_CANONICAL.get(lowered, lowered)


def skills_match(required: str, candidate_skill: str) -> bool:
    """Check whether a required skill matches a candidate's skill.

    Handles:
    1. Exact canonical match (after normalization).
    2. Substring containment as a fallback (case-insensitive).

    >>> skills_match("PostgreSQL", "Postgres")
    True
    >>> skills_match("React", "React.js")
    True
    >>> skills_match("Python", "Java")
    False
    """
    canon_req = normalize_skill(required)
    canon_cand = normalize_skill(candidate_skill)

    # Exact canonical match
    if canon_req == canon_cand:
        return True

    # Substring containment fallback (covers partial matches like
    # "GraphQL APIs" matching "GraphQL")
    req_lower = required.strip().lower()
    cand_lower = candidate_skill.strip().lower()
    if req_lower in cand_lower or cand_lower in req_lower:
        return True

    return False
