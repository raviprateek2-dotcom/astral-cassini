# 🎯 PRO HR (Astral Cassini) — Interview Preparation Guide

> **How to use this guide:** Read each question aloud and answer from memory. The goal is fluency, not memorization. Focus on the *why* behind every decision.

---

## ⚡ Elevator Pitch (First 30 Seconds)

> *"PRO HR is an end-to-end, AI-native recruitment automation platform. It orchestrates a multi-agent pipeline — from drafting job descriptions and sourcing candidates, all the way to conducting automated interviews and generating final hire/no-hire decisions. It's built on a LangGraph state machine for precise human-in-the-loop control, a FastAPI backend with real-time WebSocket streaming, and a Next.js dashboard. The entire system passes 150 automated tests and compiles to a production build in under 25 seconds."*

---

## 1. 🏛️ Architecture & Tech Stack

**Q: Walk me through the overall architecture of the system.**
> **Answer:** The system has three layers. The **frontend** is a Next.js 16 app using the App Router and a custom `useWebSocket` hook for real-time updates. The **backend** is a FastAPI server running asynchronously on Uvicorn, with SQLAlchemy managing a SQLite database (easily upgradeable to PostgreSQL). The **intelligence layer** is a LangGraph state machine that orchestrates 10+ specialized AI agents, each with a single responsibility — from JD Architect to Final Decider.

---

**Q: Why FastAPI over Django or Express/Node.js?**
> **Answer:** Two reasons. First, the entire AI ecosystem — LangChain, LangGraph, PyMuPDF — is Python-native, so a Python backend eliminates any cross-language integration overhead. Second, FastAPI's `asyncio`-first design means long-running LLM calls (which can take 3-10 seconds) do not block other HTTP requests. Django's synchronous ORM would create bottlenecks under concurrent agent execution.

---

**Q: Why SQLite? Isn't that a toy database?**
> **Answer:** It's a deliberate choice for this stage. SQLite is portable and requires zero infrastructure. The critical design decision is that we abstracted 100% of our database access through **SQLAlchemy ORM**. The database connection string lives in a single `.env` variable. Switching to PostgreSQL for production is literally one line of configuration. The schema is managed by **Alembic migrations**, so all DDL changes are versioned and reproducible.

---

**Q: Why Next.js with Turbopack instead of Vite or Create React App?**
> **Answer:** Next.js App Router lets us mix Server Components (for fast initial HTML delivery) with Client Components (for our live WebSocket dashboard). Turbopack cut our hot-reload time dramatically during development. The production build compiles all 15 routes and runs full TypeScript checking in under 25 seconds total.

---

## 2. 🤖 Artificial Intelligence & Agents

**Q: Walk me through the full pipeline from start to finish.**
> **Answer:** It has 9 stages:
> 1. **Intake** — HR creates a job requisition via the UI.
> 2. **JD Drafting** — The Architect agent drafts a full, structured job description.
> 3. **JD Review (HITL)** — The pipeline pauses. An HR manager approves or rejects the draft.
> 4. **Sourcing** — The Scout agent runs semantic + BM25 search across the resume database.
> 5. **Screening** — The Screener agent scores each candidate across 4 dimensions: skills, experience, education, and cultural fit.
> 6. **Shortlist Review (HITL)** — The pipeline pauses again for human approval of the shortlist.
> 7. **Outreach & Engagement** — The system sends personalized emails via SendGrid and classifies response intent (interested / declined / questions / reschedule).
> 8. **Interviewing** — The Coordinator schedules slots via Google Calendar; the Interviewer agent conducts structured interviews and produces scored transcripts.
> 9. **Decision & Offer (HITL)** — The Decider generates final hire/no-hire recommendations with confidence scores. Approved candidates receive an AI-generated offer letter.

---

**Q: How do you prevent the AI from hallucinating scores or making up data?**
> **Answer:** Three layers of protection:
> 1. **Structured Outputs:** Every LLM call uses LangChain's `.with_structured_output(PydanticModel)`. The LLM is forced to return JSON matching an exact schema.
> 2. **Grounding:** The Screener agent receives the *actual extracted resume text* (via PyMuPDF) and the *actual job requirements*. Scores use a weighted formula, not LLM guesswork.
> 3. **Critic Loop:** The JD Architect's output is reviewed by a separate Critic agent. If the draft scores below a threshold, the pipeline loops back automatically.

---

**Q: Why LangGraph instead of CrewAI or simple sequential chaining?**
> **Answer:** Three things LangGraph provides that alternatives do not:
> 1. **Stateful Persistence:** LangGraph serializes the entire `SharedState` to our database. The pipeline can sleep for days waiting for human approval and resume without data loss.
> 2. **Conditional Branching:** If the Critic rejects a JD, we route back to the Architect. This is a cycle — a linear chain cannot express this.
> 3. **HITL Breakpoints:** LangGraph has native "interrupt before node" support. This is how we implement the three approval gates without any workarounds.

---

**Q: How does resume parsing and matching work technically?**
> **Answer:** Candidates upload PDFs. **PyMuPDF** extracts raw text in milliseconds. We then run a two-phase match:
> - **Phase 1 — BM25 Retrieval:** Rank-BM25 does fast lexical keyword matching to identify the top 10 candidate pool.
> - **Phase 2 — LLM Re-ranking:** The Reranker agent uses `gpt-4o-mini` concurrently via `asyncio.gather` with a semaphore of 5 to deep-evaluate each candidate, returning `matching_skills`, `missing_skills`, and a `match_reason`.

---

**Q: What is the Skill Synonyms system?**
> **Answer:** We built a `skill_synonyms.py` module with a `skills_match()` function that maps equivalent terms — `"ML"` matches `"Machine Learning"`, `"JS"` matches `"JavaScript"`, `"k8s"` matches `"Kubernetes"`. This prevents false negatives where a qualified candidate is marked as missing a skill simply because they used an abbreviation on their resume.

---

## 3. Real-Time WebSocket Integration

**Q: How does the dashboard update live without refreshing?**
> **Answer:** FastAPI manages WebSocket connections per job ID. As each LangGraph agent node completes, it writes to the database and simultaneously broadcasts a JSON heartbeat over the WebSocket. The Next.js frontend has a custom `useWebSocket` hook that listens for these events and triggers a `silentRefetch` — pulling fresh data from the REST API without causing disruptive UI notifications.

---

**Q: What was the hardest bug you fixed in this project?**
> **Answer:** The WebSocket infinite render loop on the Dashboard. When a WebSocket event arrived, it called `refetch()`, which fired a `toast.success("Dashboard Updated")` notification. In React, showing a toast is a state change, which triggered a re-render, which saw the WebSocket event and fired `refetch()` again — infinite loop.
>
> The fix was to create a memoized `silentRefetch` function (via `useCallback`) that reloads data without triggering toast notifications. WebSocket events now call `silentRefetch()` while the manual refresh button still calls `refetch()`.

---

**Q: How do you secure WebSocket connections? You cannot send headers over a WebSocket.**
> **Answer:** Correct — browsers do not allow custom headers on WebSocket upgrades. We implemented a **short-lived ticket system**. The frontend first makes an authenticated REST `GET /api/auth/ws-ticket` request, returning a signed JWT expiring in 60 seconds. The frontend passes this token as a URL query parameter when establishing the WebSocket connection. The backend validates the token on the handshake before accepting.

---

## 4. Security & Error Handling

**Q: How do you handle authentication and authorization?**
> **Answer:** JWTs are signed with `python-jose` using HS256. Passwords are hashed using `bcrypt` via `passlib`. We have 4 roles: `admin`, `hr_manager`, `business_lead`, and `viewer`. Every API route checks the decoded JWT for the appropriate role. For development, `AUTH_DISABLED=true` in `.env` bypasses auth entirely without touching any application code.

---

**Q: What happens if an OpenAI API call fails mid-pipeline?**
> **Answer:** The pipeline fails gracefully at the node level. The `current_stage` is persisted before any LLM call, so the system knows exactly where it stopped. An admin can retry the specific stage without losing prior work. We also have `MOCK_AGENTS=true` mode, which replaces all LLM calls with deterministic responses — this is how all 150 tests pass without any API keys or network access.

---

**Q: What happens to candidate data? Is it private?**
> **Answer:** All data is stored locally in the SQLite database. Data is only sent externally to: (1) the OpenAI API under their standard DPA, and (2) SendGrid for email delivery. In production, we would add GDPR-compliant deletion endpoints, data retention policies, and encrypt PII fields at rest using column-level encryption.

---

## 5. Bias, Fairness & Ethics *(Critical for HR AI)*

**Q: How does your AI avoid discriminating against candidates based on gender, age, or race?**
> **Answer:** Several deliberate design choices address this:
> 1. **Transcript Anonymization:** Before interview transcripts are evaluated, we strip candidate names and replace gendered pronouns (`he/she/him/her`) with `they/them` using regex, reducing unconscious bias in the AI's assessment.
> 2. **Structured Scoring:** The Screener uses a deterministic, formula-based scoring system. Bias-prone attributes (name, age, photo) are never part of the input — only skills, experience years, and education are evaluated.
> 3. **JD Bias Audit:** The Architect agent includes a `bias_audit` section in its output, flagging gendered or exclusionary language in the drafted job description before it is published.

---

**Q: What if the AI makes a wrong hiring decision?**
> **Answer:** The AI never makes the *final* decision — a human always does. The system produces `hire`, `no_hire`, and `maybe` *recommendations* with explicit confidence scores and reasoning. All three Human-in-the-Loop checkpoints require a manager to actively approve before the pipeline advances. The immutable **Audit Trail** logs every agent action, creating a complete compliance record that can be reviewed if a decision is ever challenged.

---

**Q: What are the ethical risks of this system?**
> **Answer:** Three key risks:
> 1. **Feedback Loops:** If historical resume data reflects past biased hiring, the AI could perpetuate it. Mitigation: regularly audit match scores across demographic groups.
> 2. **Over-reliance on AI:** HR managers might rubber-stamp AI recommendations without critical review. Mitigation: the UI surfaces the AI's reasoning and uncertainty, not just the final decision.
> 3. **Data Privacy:** Resumes contain highly personal information. Mitigation: strict data retention policies, role-based access control, and encrypted storage in production.

---

## 6. Scalability & System Design

**Q: How would you scale this to 10,000 applicants per day?**
> **Answer:**
> 1. **Database:** Swap SQLite for a managed PostgreSQL instance via SQLAlchemy. Add read replicas for the analytics dashboard.
> 2. **Task Queue:** Offload LangGraph execution to Celery + Redis, decoupling pipeline processing from API response times.
> 3. **Resume Search:** Replace BM25 with a Vector Database (Pinecone or pgvector) for sub-millisecond semantic similarity search across millions of resumes.
> 4. **WebSockets:** Implement Redis Pub/Sub to broadcast events across multiple FastAPI instances behind a load balancer.
> 5. **LLM Cost:** Fine-tune a smaller open-source model (e.g., Llama 3) on HR screening data to reduce OpenAI API costs by 80%+.

---

**Q: How would you add a mobile app to this system?**
> **Answer:** The FastAPI backend is a fully RESTful API, completely decoupled from the Next.js frontend. A React Native or Flutter mobile app could consume the same API endpoints. The only addition needed would be push notifications via Firebase Cloud Messaging to replace browser toast notifications.

---

## 7. Live Demo Walkthrough Script

*If the interviewer asks you to share your screen:*

1. Start servers: `cd backend && python -m uvicorn app.main:app --port 8000` and `cd frontend && npm run dev`
2. Open `http://localhost:3000`
3. **Dashboard:** *"Here you can see all active pipelines, candidate counts, and live agent health status."*
4. **Kanban:** *"A visual Kanban board showing all jobs at each pipeline stage in real time."*
5. **Jobs > New Job:** Create a new job titled "Senior AI Engineer" in Engineering.
6. **Audit Trail:** *"Every AI agent action is logged here in real time — completely immutable and timestamped."*
7. **Candidates:** *"All scored candidates with match percentages, strengths, and skill gaps."*
8. **Decisions:** *"The Decider agent's final recommendations with confidence weightings and reasoning."*
9. **Export CSV:** *"Everything is exportable for HR compliance records."*

---

## 8. Key Metrics to Quote

| Metric | Value |
|---|---|
| Total automated tests | **150 (all passing, 0 failures)** |
| Test suite execution time | **~11.7 seconds** |
| Frontend production compile time | **~11 seconds (Turbopack)** |
| TypeScript check time | **~13.7 seconds** |
| Static routes pre-rendered | **15 routes** |
| Pipeline stages | **9 stages, 10+ specialized AI agents** |
| Frontend lint errors | **0 errors (5 minor warnings)** |
| Concurrent re-ranking | **asyncio.gather, semaphore of 5** |
| WebSocket latency (local) | **< 50ms** |
| Skill synonym mappings | **Custom module covering 30+ tech term pairs** |

---

## 9. Behavioral Questions

**Q: What would you improve if you had more time?**
> *"Three things: (1) Replace BM25 with a proper vector database for semantic resume search. (2) Fine-tune a smaller open-source LLM on HR data to reduce OpenAI API dependency. (3) Add a candidate-facing portal so applicants can track their own application status in real time."*

---

**Q: What was your biggest challenge?**
> *"The Human-in-the-Loop state persistence in LangGraph. The pipeline needs to pause for days waiting for manager approval and resume exactly where it stopped — with all candidates, scores, and transcripts intact. Serializing the entire SharedState to the database and hydrating it back without losing any LangGraph graph structure required very careful schema design."*

---

**Q: How did you divide responsibilities between the AI agents?**
> *"We followed the Single Responsibility Principle. Each agent does exactly one thing: the Architect drafts, the Critic reviews, the Scout searches, the Screener scores. This makes each agent independently testable and replaceable. If we want to swap OpenAI for Anthropic on just the screening step, we change one file."*

---

**Q: Did you work on this alone or in a team?**
> *"I built this project with the assistance of an AI coding assistant, which helped me implement boilerplate and debug issues. However, all architectural decisions, agent design, pipeline logic, and system design were directed and owned by me."*

---

> You built something genuinely impressive. Own every decision with confidence — you know this system inside out.
