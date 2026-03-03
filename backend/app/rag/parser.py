"""Improved RAG Parser — Section-aware resume parsing.

Improvement over v1:
- Splits resume into labelled sections (Skills, Experience, Education, Summary)
- Stores each section as a separate ChromaDB chunk → finer-grained retrieval
- Extracts structured metadata (years, titles, companies) for pre-filtering
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Section detection helpers
# ---------------------------------------------------------------------------

SECTION_PATTERNS = {
    "summary": re.compile(
        r"(?i)\b(summary|objective|profile|about me|professional summary)\b",
    ),
    "skills": re.compile(
        r"(?i)\b(skills|technical skills|core competencies|technologies|tech stack)\b",
    ),
    "experience": re.compile(
        r"(?i)\b(experience|work experience|employment|career history|professional experience)\b",
    ),
    "education": re.compile(
        r"(?i)\b(education|academic|qualifications|degrees?)\b",
    ),
    "projects": re.compile(
        r"(?i)\b(projects?|portfolio|open[- ]source)\b",
    ),
    "certifications": re.compile(
        r"(?i)\b(certifications?|licenses?|awards?|achievements?)\b",
    ),
}

SKILLS_KEYWORDS = [
    "python", "java", "javascript", "typescript", "go", "rust", "c\\+\\+", "c#",
    "react", "next", "vue", "angular", "node", "fastapi", "django", "flask", "spring",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "gcp", "azure", "kubernetes", "docker", "terraform", "ci/cd",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit",
    "langchain", "langgraph", "openai", "llm", "rag", "chromadb", "pinecone",
    "git", "linux", "agile", "scrum",
]

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
NAME_RE = re.compile(r"^([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)")
EXPERIENCE_YEARS_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)", re.I)

# ---------------------------------------------------------------------------
# Section-aware text splitter
# ---------------------------------------------------------------------------

def _split_into_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.setdefault(current_section, []).append("")
            continue

        # Check if this line is a section header
        matched_section = None
        for section_name, pattern in SECTION_PATTERNS.items():
            if pattern.search(stripped) and len(stripped) < 60:
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def _extract_skills(text: str) -> list[str]:
    """Extract tech skills from text using keyword matching."""
    found = []
    lower = text.lower()
    for kw in SKILLS_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", lower):
            found.append(kw.replace("\\+\\+", "++"))
    return list(dict.fromkeys(found))  # deduplicated, order-preserved


def _extract_experience_years(text: str) -> int:
    """Extract claimed years of experience from resume text."""
    matches = EXPERIENCE_YEARS_RE.findall(text)
    if matches:
        return max(int(m) for m in matches)
    return 0


# ---------------------------------------------------------------------------
# PDF parser (PyMuPDF)
# ---------------------------------------------------------------------------

def parse_resume_pdf(file_path: str) -> dict:
    """Parse a PDF resume into structured sections.

    Returns a dict with:
    - name, email, phone
    - skills (list)
    - experience_years (int)
    - sections (dict of section_name → text)
    - resume_text (full concatenated text)
    - chunks (list of dicts, each a section for embedding)
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        pages_text = [page.get_text("text") for page in doc]
        doc.close()
        full_text = "\n".join(pages_text)

    except Exception as e:
        logger.warning(f"PyMuPDF failed for {file_path}: {e}. Using fallback.")
        try:
            with open(file_path, "rb") as f:
                full_text = f.read().decode("utf-8", errors="ignore")
        except Exception:
            full_text = ""

    return _build_parsed_result(full_text, source_file=Path(file_path).name)


def parse_resume_text(text: str) -> dict:
    """Parse a plain-text resume."""
    return _build_parsed_result(text, source_file="text_input")


def _build_parsed_result(full_text: str, source_file: str) -> dict:
    """Core parsing logic shared by PDF and text parsers."""
    sections = _split_into_sections(full_text)

    # Extract metadata
    name_match = NAME_RE.search(full_text.strip())
    name = name_match.group(1) if name_match else "Unknown Candidate"

    email_match = EMAIL_RE.search(full_text)
    email = email_match.group(0) if email_match else ""

    phone_match = PHONE_RE.search(full_text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # Skills from the dedicated section first, then full text
    skills_text = sections.get("skills", "") + " " + full_text
    skills = _extract_skills(skills_text)

    experience_years = _extract_experience_years(
        sections.get("experience", full_text)
    )

    # Build embedding chunks (one per section)
    chunks = []
    for section_name, section_text in sections.items():
        if section_text.strip():
            chunks.append({
                "section": section_name,
                "text": section_text,
                "metadata": {
                    "section": section_name,
                    "source_file": source_file,
                    "candidate_name": name,
                },
            })

    # If no sections detected, treat entire text as one chunk
    if not chunks:
        chunks = [{
            "section": "full",
            "text": full_text,
            "metadata": {"section": "full", "source_file": source_file, "candidate_name": name},
        }]

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience_years": experience_years,
        "education": sections.get("education", ""),
        "sections": sections,
        "resume_text": full_text[:2000],  # full text for fallback
        "chunks": chunks,
        "source_file": source_file,
    }
