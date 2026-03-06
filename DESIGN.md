# Design Document — Multi-Agent Research System

## 1. Architecture Overview

The system is a **four-agent async pipeline** backed by FastAPI and rendered live in a React dashboard.

```
User Query
    │  POST /run (or /tasks)
    ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI  (api/routes.py)                                   │
│  asyncio.create_task() → returns immediately (<5 ms)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator  (orchestrator/orchestrator.py)               │
│                                                             │
│  [Planner] → asyncio.gather([Researcher×N]) → [Writer]      │
│                                    ↕ revision loop (≤3×)    │
│                              [Reviewer]                     │
│                                                             │
│  Every step timed, persisted to SQLite, status updated      │
└─────────────────────┬───────────────────────────────────────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
       SQLite (SQLModel)   LLM Client
       task_store.py       (Gemini / OpenAI / Ollama)
                           exponential backoff (3s → 6s → 12s)
```

The React frontend polls `GET /task/{id}` every 1.5 s, reflecting the pipeline status in real time without WebSockets.

---

## 2. Agent Design Reasoning

All agents share one abstract base class (`Agent` ABC) with two abstract members — `name` (property) and `async run()`. This contract ensures every agent is:
- **Async-first** — compatible with `asyncio.gather()`
- **Identifiable** — `name` drives step logging and pipeline dispatch
- **Replaceable** — the orchestrator never inspects agent internals, only calls `run()` and reads `AgentResult`

| Agent | Responsibility | Key design choice |
|---|---|---|
| **Planner** | Decomposes query into 3 focused subtopics | Max 100 tokens; hard cap at `subtasks[:3]` |
| **Researcher** | Collects 3 facts per subtopic (parallel) | Semaphore-limited concurrency (3 cloud / 1 Ollama) |
| **Fact Checker** | Re-validates research before writing (optional) | Same JSON contract as Researcher; no Writer changes |
| **Writer** | Synthesises research → Markdown report | Grounded strictly to researcher facts; 150-word cap |
| **Reviewer** | Quality gate with structured APPROVED / REVISION_NEEDED verdict | Default to APPROVED; fail-open on ambiguity |

Agents are registered in `agents/registry.py`. Adding a new agent requires only creating the class and adding one entry to `AGENT_REGISTRY` — no changes to existing agents or the orchestrator's dispatch table.

---

## 3. Orchestrator Design

The `Orchestrator` class owns the full pipeline lifecycle:

1. **`create_task()`** — allocates a UUID, sets `status="planning"`, persists to SQLite, returns immediately.
2. **`run()`** — iterates over the agent list; each stage returns an updated `PipelineContext` (immutable input → output pattern). The Reviewer is treated specially: it enters a revision loop that calls the Writer again if `status == "revision_needed"`, capped at `MAX_REVISIONS = 3` to prevent infinite loops.
3. **`_timed(coro)`** — wraps every agent call to capture wall-clock start time and elapsed milliseconds stored in `Step`.
4. Every status transition (`planning → researching → writing → reviewing → completed`) calls `save_task()` immediately so polls always see fresh state.

The orchestrator is stateless between requests — all mutable state lives in `Task` / `PipelineContext`, enabling safe concurrent pipeline runs.

---

## 4. Data Flow

```
POST /run
  └─ create_task()  →  SQLite (status=planning)
  └─ asyncio.create_task(orchestrator.run(id))
  └─ return Task immediately

orchestrator.run()
  ├─ PlannerAgent.run(query)        → subtasks: ["topic1", "topic2", "topic3"]
  │                                   save_task(status=researching)
  ├─ asyncio.gather(
  │      ResearcherAgent("topic1")  → {topic, facts[]}
  │      ResearcherAgent("topic2")  → {topic, facts[]}
  │      ResearcherAgent("topic3")  → {topic, facts[]}
  │  )                               save_task(status=writing)
  ├─ WriterAgent(query, subtasks, research)  → Markdown draft
  │                                           save_task(status=reviewing)
  └─ ReviewerAgent(draft)
       ├─ approved  →  save_task(status=completed, result=draft)
       └─ revision_needed  →  WriterAgent(revised) → ReviewerAgent (loop ≤3×)

Frontend polling (every 1.5 s)
  GET /task/{id}  →  latest Task JSON  →  React state update
```

---

## 5. Trade-offs

### Polling vs WebSockets
Polling was chosen for simplicity and robustness. Every `GET /task/{id}` returns the full task state — no connection management, heartbeats, or reconnection logic. The 1.5 s interval is imperceptible in UX terms given pipeline steps take seconds each. The trade-off is minor over-fetching. WebSocket push would reduce latency to near-zero but adds server-side connection tracking and frontend reconnect logic. This is a clear future improvement documented in `README.md §12`.

### Synchronous vs Asynchronous Execution
The pipeline is fully async (`asyncio`). The HTTP response to `POST /run` returns in < 5 ms; the pipeline runs as a background task. This means the server can handle many concurrent requests — polling calls are never blocked by a running pipeline. The trade-off is that errors in background tasks must be caught explicitly (handled in the orchestrator's `try/except` which sets `status="error"`).

### SQLite vs In-Memory Dict
SQLite was chosen over a plain dict to persist tasks across API calls within a server session and to power the Recent Tasks history panel. It adds no external infrastructure dependency. The trade-off vs Redis/PostgreSQL is that tasks are lost on server restart and multi-instance deployments are not supported.

### Chosen Frameworks
- **FastAPI** — native async support, automatic OpenAPI docs, Pydantic validation out of the box
- **React + Vite** — fast HMR, tree-shaking, and Tailwind CSS first-class; minimal config vs Next.js for a pure SPA
- **SQLModel** — Pydantic + SQLAlchemy in one; the `TaskRow` table mirrors the `Task` Pydantic model with JSON columns for nested data

---

## 6. Assumptions

- The LLM is reliable enough that a 3-retry policy with 3 s / 6 s / 12 s backoff covers transient failures.
- Research subtopics are always independent — no inter-topic dependency that would require a DAG scheduler.
- Reports at ~150 words satisfy the use-case; deeper coverage can be addressed by increasing `max_tokens` or adding more subtopics.
- A single-user local deployment is the primary target; no authentication, rate limiting, or multi-tenancy is built in.

---

## 7. What I'd Improve With More Time

1. **WebSocket / SSE** — push each `Step` completion event to the frontend the moment it occurs, eliminating polling.
2. **DAG-based pipeline scheduler** — express agent dependencies as a graph rather than a linear list, enabling conditional branches and parallel writer tasks.
3. **Streaming LLM output** — render the report token-by-token rather than waiting for the full response.
4. **User-configurable pipelines in UI** — drag-and-drop agent ordering, per-agent model selection.
5. **Redis task store** — survive server restarts and support horizontal scaling.
6. **Authentication** — API key or OAuth for the backend to control access.
7. **Evaluation harness** — track report quality metrics over time (completeness, accuracy, reading level) to measure the impact of model/prompt changes.
