# Astral Cassini (PRO HR) - Tech Stack

This document outlines the complete, full-stack architecture of the Astral Cassini (PRO HR) project.

## 1. Frontend (User Interface)
* **Framework:** **Next.js 16** (React) utilizing the App Router.
* **Build System:** **Turbopack** for ultra-fast local compilation and Hot Module Replacement (HMR).
* **Styling:** **Vanilla CSS** and CSS Modules (`globals.css` and `.module.css` files), focusing on modern glassmorphism UI, dynamic CSS grid/flexbox layouts, and minimal dependencies (no Tailwind).
* **State & Real-time:** 
  * Native React hooks (`useState`, `useEffect`) alongside custom hooks like `useJobStore`.
  * **WebSockets** (`useWebSocket` hook) for real-time, bi-directional event streaming from the backend to ensure the dashboard updates live without page refreshes.

## 2. Backend (API & Orchestration)
* **Web Framework:** **FastAPI** (Python 3.14), serving highly concurrent, asynchronous REST and WebSocket endpoints.
* **Server:** **Uvicorn** running ASGI for high performance.
* **Database & ORM:** 
  * **SQLite** for lightweight, file-based relational data storage (`prohr.db`).
  * **SQLAlchemy 2.0** as the ORM to map Python classes to database tables.
  * **Alembic** to manage database schema migrations.
* **Security:** `passlib`, `bcrypt`, and `python-jose` for JWT-based authentication and password hashing.

## 3. Artificial Intelligence & Agents
* **Orchestration:** **LangGraph** manages the state machine, agent routing, and Human-in-the-Loop (HITL) approval breakpoints.
* **LLM Integration:** **LangChain** (`langchain`, `langchain-openai`) to interface with Large Language Models, bind custom tools, and enforce strict structured JSON outputs (`.with_structured_output()`).
* **Underlying Models:** Defaults to **OpenAI** (e.g., `gpt-4o-mini`), though configurable.
* **Information Retrieval (RAG):** **Rank-BM25** is used for lexical search/scoring of candidate skills against job requirements.

## 4. Third-Party Tool Integrations
The AI agents are equipped with several external integrations to perform their tasks:
* **Resume Parsing:** **PyMuPDF** (`fitz`) for extracting raw text from candidate PDF resumes.
* **Communications:** **SendGrid API** for sending dynamic outreach emails to candidates.
* **Scheduling:** **Google Calendar API** (`google-api-python-client`) for checking availability and scheduling interview slots.
