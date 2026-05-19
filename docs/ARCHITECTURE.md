# PRO HR Architecture

## Overview
PRO HR is a full-stack, AI-driven recruitment platform. It leverages an autonomous multi-agent system to handle job requisition drafting, candidate sourcing, screening, interview scheduling, and final hiring decisions.

## Tech Stack
* **Frontend**: Next.js 16 (App Router), React, TypeScript.
* **Backend**: FastAPI, Python 3.14.
* **Database**: SQLite (via SQLAlchemy) for relational data.
* **AI/Orchestration**: LangChain, OpenAI APIs.
* **Vector Store**: FAISS for Resume Retrieval-Augmented Generation (RAG).

## Multi-Agent Topology
The core intelligence of PRO HR is a deterministic state machine managed by `backend/app/core/orchestrator.py`, moving through 7 specialized agent nodes:

1. **System Node**: Initializes the pipeline.
2. **JD Architect (Agent 1)**: Generates a structured Job Description based on initial user inputs.
3. **The Liaison (Agent 2)**: Re-formats and approves the finalized JD.
4. **The Scout (Agent 3)**: Uses FAISS RAG to query embedded resumes and sources relevant candidates.
5. **The Screener (Agent 4)**: Evaluates candidates against the JD, generating structured scores (e.g., technical, cultural).
6. **The Coordinator (Agent 7)**: Automates interview scheduling and logs interview assessments.
7. **The Decider (Agent 6)**: Reviews all scores and interview feedback to make final hiring recommendations.
8. **Human Reviewer**: Intervenes at manual gating steps (e.g., JD approval, Shortlist confirmation).

## Deterministic State Machine Flow
Pipelines follow strict progression:
`jd_drafting` -> `jd_review` -> `sourcing` -> `screening` -> `shortlist_review` -> `interviewing` -> `decision` -> `hire_review` -> `completed`

Transitions are guarded by API calls.

## Database Schema
* **User**: Manages system access (email, hashed_password, role, department).
* **Job**: Represents a recruitment pipeline. Stores `job_id`, `job_title`, `department`, `current_stage`, `workflow_state` (JSON blob containing candidates, scores, and draft data).
* **WebSocket Tokens**: Short-lived JWTs are generated to securely establish real-time feeds without exposing persistent session cookies.
