# PRO HR — Autonomous Multi-Agent Recruitment Ecosystem

A multi-agent recruitment platform powered by **LangGraph** with **7 specialized AI agents** for end-to-end hiring automation.

## 🏗️ Architecture

```
Frontend (Next.js 15)  →  FastAPI Backend  →  LangGraph Orchestrator
                                                    ↓
                                            7 Autonomous Agents
                                                    ↓
                                          ChromaDB Vector Store (RAG)
```

### The 7 Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **JD Architect** | Drafts bias-aware job descriptions |
| 2 | **The Liaison** | Human-in-the-loop approval gatekeeper |
| 3 | **The Scout** | Semantic resume search via RAG |
| 4 | **The Screener** | Gap analysis & scoring (0-100) |
| 5 | **The Coordinator** | Interview scheduling |
| 6 | **The Interviewer** | Transcript competency assessment |
| 7 | **The Decider** | Final hire/no-hire recommendations |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API Key

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Backend runs at **<http://localhost:8000>** (API docs: `/docs`)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at **<http://localhost:3000>**

## 📱 Dashboard Pages

- **Dashboard** — Overview metrics, active pipelines, agent roster
- **Jobs** — Create job requisitions, view generated JDs
- **Candidates** — Scored candidate cards with gap analysis
- **Approvals** — HITL gates for JD, shortlist, and hire decisions
- **Interviews** — Scheduled interviews and competency assessments
- **Decisions** — Final hire/no-hire with explainable reasoning
- **Audit Trail** — Timeline of all agent actions and decisions

## 🔑 Key Features

- **Bias Mitigation** — Guardrails in all agent prompts
- **Explainable Scoring** — Transparent 4-dimension candidate evaluation
- **HITL Gates** — 3 human approval checkpoints in the pipeline
- **RAG Search** — Semantic resume matching with ChromaDB
- **Audit Trail** — Complete decision history with agent attribution

## 🛠️ Tech Stack

- **Orchestration**: LangGraph with checkpointed workflows
- **LLM**: OpenAI GPT-4o
- **Backend**: FastAPI + Python 3.11
- **Vector DB**: ChromaDB (local, swap to Pinecone for prod)
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Real-time**: WebSocket for live agent status updates
