# Parallel Multi-Agent AI System

> A production-ready multi-agent architecture that decomposes complex queries into parallel research, writing, and review workflows — delivering structured AI-generated reports in a fraction of the time of sequential pipelines.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20%7C%20Gemini%20%7C%20OpenAI-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Descriptions](#agent-descriptions)
4. [Parallel Processing Design](#parallel-processing-design)
5. [System Workflow](#system-workflow)
6. [Example Pipeline Flow](#example-pipeline-flow)
7. [Performance & Benefits](#performance--benefits)
8. [Tech Stack](#tech-stack)
9. [Project Structure](#project-structure)
10. [Getting Started](#getting-started)
11. [Configuration](#configuration)
12. [API Reference](#api-reference)
13. [Future Improvements](#future-improvements)

---

## Overview

The Parallel Multi-Agent AI System is a full-stack application that accepts a natural-language query, automatically decomposes it into subtopics, and processes each subtopic through a coordinated pipeline of specialised AI agents. The system is designed around **parallelism** as a first-class concern — research and writing tasks for independent topics are executed concurrently, not sequentially.

**What it does:**

- Accepts any open-ended query (e.g. *"Compare microservices vs monoliths"*)
- Automatically identifies 3 focused research subtopics
- Researches all subtopics simultaneously using parallel agents
- Synthesises findings into a structured Markdown report
- Enforces quality through an automated review gate
- Streams live status updates to the UI as each stage completes

**Who it is for:**

Developers, researchers, and teams who need to automate structured knowledge synthesis at scale, or who want a reference architecture for building reliable multi-agent LLM systems.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          React Frontend                         │
│            (Vite · Tailwind CSS · real-time polling)            │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTP via Vite proxy (no CORS)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend :8001                        │
│                                                                 │
│   POST /run ──► Orchestrator ──► Task Store (in-memory)         │
│   GET  /task/{id}              ◄── polling                      │
│   GET  /health                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Orchestrator  │  Coordinates all agents
                    │     Agent       │  Manages status lifecycle
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Planner    │  │  Researcher │  │   Writer    │
    │   Agent     │  │  Agent ×N   │  │   Agent     │
    └─────────────┘  └─────────────┘  └─────────────┘
           │         (parallel)              │
           │                                 ▼
           │                        ┌─────────────────┐
           └───────────────────────►│  Reviewer Agent │
                                    └─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  LLM Client     │
                                    │  (Ollama/Gemini/ │
                                    │   OpenAI)        │
                                    └─────────────────┘
```

The backend is fully asynchronous (`asyncio`). Every agent communicates through a shared `generate(prompt, max_tokens)` interface, making the LLM provider completely swappable via a single environment variable.

---

## Agent Descriptions

### 1. Planner Agent

The entry point of every pipeline run. It receives the raw user query and produces a structured list of focused subtopics to research.

**Responsibilities:**
- Parses the user's query using an LLM call
- Returns a JSON array of exactly **3 concise subtopic strings**
- Acts as the decomposition layer — turns one broad question into actionable research tasks

**Design:**
- Uses a tightly constrained prompt to force a valid JSON array response
- Hard-capped at 3 subtasks (`subtasks[:3]`) to ensure consistent concurrency
- `max_tokens=150` — a JSON array of 3 short strings needs very few tokens

```python
prompt = (
    "Break the following task into exactly 3 research subtasks. "
    "Return ONLY a JSON array of 3 short strings, no explanation.\n"
    f"Task: {input_data}"
)
response = await generate(prompt, max_tokens=150)
```

---

### 2. Research Agent

One Research Agent instance is spawned per subtopic. All instances execute **concurrently**, making the total research time equal to the time of a single research call rather than N times that.

**Responsibilities:**
- Accepts one subtopic string
- Queries the LLM for key facts about that subtopic
- Returns concise, factual bullet points for use by the Writer

**Design:**
- Controlled by `asyncio.Semaphore(3)` — allows all 3 agents to run simultaneously while bounding Ollama connection load
- `max_tokens=400` — enough for 3 focused bullet points without over-generating
- Subtopic label is stored alongside the output in the `Step` model for timeline display

```python
research_semaphore = asyncio.Semaphore(3)

async with research_semaphore:
    prompt = (
        f"Topic: {subtask}\n\n"
        "Give 3 concise bullet points of key facts. Be brief."
    )
    result = await generate(prompt, max_tokens=400)
```

---

### 3. Writer Agent

Receives all research outputs together and synthesises them into a single, coherent Markdown report. Uses **dynamic prompting** — the full research context is injected as part of the prompt, so the Writer can draw relationships across subtopics.

**Responsibilities:**
- Combines research notes from all N Research Agents
- Produces a structured Markdown report with `##` headings per topic
- Includes an introduction and a brief conclusion
- Output is passed directly to the Reviewer

**Design:**
- Dynamic prompt construction: research notes are joined and embedded at call time
- `max_tokens=900` — sufficient for a complete multi-section report
- Prompt is concise by design to avoid directing the model toward verbose over-generation

```python
notes = "\n\n".join(research_outputs)
prompt = (
    f"User Request: {user_query}\n\n"
    f"Research Notes:\n{notes}\n\n"
    "Write a clear Markdown report answering the request. "
    "Use ## headings for each topic, a short intro, and a brief conclusion. "
    "Be informative but concise."
)
report = await generate(prompt, max_tokens=900)
```

---

### 4. Reviewer Agent

The final quality gate. Reviews the Writer's draft and either approves it or returns specific, actionable feedback. If a revision is requested, the Writer re-runs with the feedback appended.

**Responsibilities:**
- Checks for factual inconsistencies and contradictory information
- Identifies logical errors and missing sections
- Evaluates structural clarity
- Returns a binary verdict: `APPROVED` or `REVISION: <specific feedback>`

**Design:**
- Forces a strict output format — the LLM cannot return anything other than the two expected patterns
- `max_tokens=150` — a one-line verdict is all that is required
- Ambiguous responses default to `APPROVED` to prevent infinite loops

```python
# Possible outputs:
"APPROVED"
"REVISION: The scalability section contradicts the intro on line 3."
```

---

### 5. Orchestrator Agent

The central coordinator. It owns the task lifecycle, wires all agents together, manages the status state machine, and records a detailed `Step` timeline for every action taken.

**Responsibilities:**
- Creates a `Task` object and persists it for polling
- Calls Planner → `asyncio.gather(Researchers)` → Writer → Reviewer in sequence
- Updates `task.status` at each stage transition (`planning → researching → writing → reviewing → done`)
- Records every step with agent name, subtask label, output, timestamp, and duration
- Attaches execution metrics at completion (`llm_calls`, `retries`, `duration_ms`)

```
Status machine:
  planning → researching → writing → reviewing → done
                                         ↑           |
                                         └───────────┘
                                    (revision loop)
```

---

## Parallel Processing Design

The system is built around `asyncio` cooperative concurrency. The critical design insight is **where** parallelism is applied:

```
Sequential (naive) approach:
  Research A → Research B → Research C → Write → Review
  Total: T_A + T_B + T_C + T_W + T_R

Parallel (this system):
  Research A ─┐
  Research B ─┼─► (all complete together) → Write → Review
  Research C ─┘
  Total: max(T_A, T_B, T_C) + T_W + T_R
```

For 3 research calls averaging 20 seconds each, the sequential approach takes ~60 seconds in the research phase alone. The parallel approach takes ~20 seconds — a **3× speedup** on the most expensive phase.

**Key mechanisms:**

| Mechanism | Purpose |
|---|---|
| `asyncio.gather(*[researcher.run(s) for s in subtasks])` | Fires all Research Agents simultaneously |
| `asyncio.Semaphore(3)` | Caps concurrent Ollama connections to match the number of subtasks |
| Per-agent `max_tokens` budgets | Prevents any single call from generating more tokens than its task requires |
| Non-blocking `httpx.AsyncClient` | All HTTP calls to Ollama are I/O-non-blocking — the event loop is never stalled |

---

## System Workflow

```
1. User submits query via the React UI
         │
         ▼
2. POST /run → backend creates Task (status: "planning")
         │
         ▼
3. Planner Agent → returns ["subtask_1", "subtask_2", "subtask_3"]
         │
         ▼
4. status → "researching"
   asyncio.gather launches 3 Research Agents in parallel
   Each agent researches its subtopic independently
         │
         ▼
5. status → "writing"
   Writer Agent receives all 3 research outputs
   Synthesises into a unified Markdown report
         │
         ▼
6. status → "reviewing"
   Reviewer Agent checks the draft
   ┌─ APPROVED → status = "done", result saved
   └─ REVISION → feedback sent back to Writer → repeat from step 5
         │
         ▼
7. Frontend polling (GET /task/{id}) detects status = "done"
   Report rendered in ReportViewer with word count and download option
   Metrics card shows: LLM Calls / Retries / Total Duration
```

---

## Example Pipeline Flow

**Input query:** `"What are the trade-offs between SQL and NoSQL databases?"`

```
[Planner]
  Subtasks: [
    "SQL database architecture and ACID properties",
    "NoSQL database types and use cases",
    "Performance and scalability comparison"
  ]

[Researcher × 3]  ← all running simultaneously
  Agent 1 → "• SQL uses structured schemas... • ACID guarantees..."
  Agent 2 → "• Document, key-value, graph stores... • Eventual consistency..."
  Agent 3 → "• SQL scales vertically... • NoSQL horizontal sharding..."

[Writer]
  ## SQL Architecture and ACID Properties
  SQL databases organise data into tables with enforced schemas...

  ## NoSQL Types and Use Cases
  NoSQL encompasses document stores (MongoDB), key-value stores (Redis)...

  ## Performance and Scalability
  SQL databases traditionally scale vertically...

  ## Conclusion
  The right choice depends on consistency requirements...

[Reviewer]
  → APPROVED

[Result]
  Full Markdown report delivered to the UI in ~75 seconds.
  Metrics: { llm_calls: 5, retries: 0, duration_ms: 74300 }
```

---

## Performance & Benefits

### Latency Reduction Through Parallelism

| Phase | Sequential Approach | This System | Improvement |
|---|---|---|---|
| Planning | ~8 s | ~8 s | — |
| Research (3 subtasks) | ~60 s | ~20 s | **3× faster** |
| Writing | ~30 s | ~30 s | — |
| Reviewing | ~8 s | ~8 s | — |
| **Total** | **~106 s** | **~66 s** | **~38% faster** |

*Timings based on `gemma3:4b` running on CPU. GPU inference will be significantly faster.*

### Token Budget Optimisation

Enforcing `max_tokens` per agent prevents the single largest source of latency in local LLM inference — unbounded generation:

| Agent | max_tokens | Reason |
|---|---|---|
| Planner | 150 | JSON array of 3 short strings |
| Researcher | 400 | 3 bullet points per subtopic |
| Writer | 900 | Full Markdown report, concise |
| Reviewer | 150 | One-line verdict only |

### Scalability

- **Horizontal topic scaling:** Adding more subtopics only increases the semaphore value and the `asyncio.gather` call — no architectural changes needed
- **Provider-agnostic:** Swap between Ollama, Gemini, and OpenAI by changing one environment variable; all agents use the same `generate()` interface
- **Stateless agents:** Each agent is a pure async function with no shared mutable state — safe to scale and test independently

### Modularity

- Each agent is an independent class with a single `async run()` method
- The LLM client is fully decoupled from agents — swapping providers requires zero agent code changes
- The Task/Step data model is provider-agnostic and can be persisted to any database

### Reliability

- Built-in retry with exponential back-off (3 s → 6 s → 12 s) on every LLM call
- HTTP 429 rate-limit detection with logged warnings
- Reviewer fallback: ambiguous responses default to `APPROVED` to prevent infinite revision loops

---

## Tech Stack

### Backend

| Technology | Role |
|---|---|
| **Python 3.11+** | Runtime |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **asyncio** | Concurrent agent execution |
| **httpx** | Async HTTP client for LLM API calls |
| **Pydantic v2** | Data validation and serialisation |
| **python-dotenv** | Environment variable management |

### Frontend

| Technology | Role |
|---|---|
| **React 18** | UI framework |
| **Vite** | Dev server and build tool (with proxy) |
| **Tailwind CSS** | Utility-first styling |
| **@tailwindcss/typography** | Markdown report prose styling |
| **react-markdown** | Render LLM Markdown output |
| **Axios** | HTTP client with Vite proxy routing |

### LLM Providers (pluggable)

| Provider | Model | Notes |
|---|---|---|
| **Ollama** (default) | `gemma3:4b` | Local, private, no API key required |
| **Google Gemini** | `gemini-2.5-flash` | Cloud, fast, requires API key |
| **OpenAI** | `gpt-4o-mini` | Cloud, requires API key |

---

## Project Structure

```
multi-agent-system/
├── README.md
├── backend/
│   ├── .env                        # Secrets and provider config (not committed)
│   ├── main.py                     # FastAPI app entry point, CORS, .env loader
│   ├── config.py                   # USE_LLM flag
│   ├── requirements.txt
│   │
│   ├── agents/
│   │   ├── base_agent.py           # Abstract Agent base class
│   │   ├── planner_agent.py        # Subtask decomposition, max_tokens=150
│   │   ├── researcher_agent.py     # Parallel research, Semaphore(3), max_tokens=400
│   │   ├── writer_agent.py         # Report synthesis, max_tokens=900
│   │   └── reviewer_agent.py       # Quality gate, max_tokens=150
│   │
│   ├── orchestrator/
│   │   └── orchestrator.py         # Pipeline wiring, status machine, metrics
│   │
│   ├── llm/
│   │   └── llm_client.py           # generate(prompt, max_tokens), retry, metrics
│   │
│   ├── models/
│   │   ├── task.py                 # Task + Step models (subtask, duration_ms)
│   │   └── agent_result.py         # AgentResult model
│   │
│   ├── api/
│   │   └── routes.py               # POST /run, GET /task/{id}, GET /health
│   │
│   └── storage/
│       └── task_store.py           # In-memory task store
│
└── frontend/
    ├── package.json
    ├── vite.config.js              # Proxy: /run, /task, /health → :8001
    ├── tailwind.config.js
    └── src/
        ├── App.jsx
        ├── index.css               # Keyframe animations, shimmer, scrollbar
        ├── pages/
        │   └── Dashboard.jsx       # Hero landing + active task layout
        ├── components/
        │   ├── TaskInput.jsx       # Glass-style query input
        │   ├── PipelineVisualizer.jsx  # Live stage tracker with agent colours
        │   ├── Timeline.jsx        # Step cards with subtask labels
        │   ├── ReportViewer.jsx    # Markdown render, word count, download
        │   ├── MetricsCard.jsx     # LLM Calls / Retries / Duration
        │   └── StatusBadge.jsx     # Status pill component
        ├── hooks/
        │   └── useTaskPolling.js   # Polls GET /task/{id} every second
        └── services/
            └── api.js              # Axios with baseURL: '' (Vite proxy)
```

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- [Ollama](https://ollama.com) installed (for local inference)

### 1. Pull the LLM model

```bash
ollama pull gemma3:4b
```

### 2. Set up the Python environment

```bash
cd multi-agent-system/backend
python -m venv ../../venv
# Windows:
../../venv/Scripts/activate
# macOS/Linux:
source ../../venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# Copy the example and fill in your values
cp .env.example .env
```

See [Configuration](#configuration) for all available variables.

### 4. Start the backend

```powershell
# Windows PowerShell
$env:PYTHONPATH = (Get-Location).Path
& "..\..\venv\Scripts\uvicorn.exe" main:app --port 8001 --reload
```

```bash
# macOS / Linux
PYTHONPATH=. uvicorn main:app --port 8001 --reload
```

### 5. Start the frontend

```bash
cd multi-agent-system/frontend
npm install
npm run dev
```

Open **http://localhost:3000** — the Vite dev server proxies all API requests to the backend automatically.

### 6. Verify

```bash
curl http://localhost:8001/health
# → {"status": "ok"}
```

---

## Configuration

All configuration lives in `backend/.env`:

```env
# ── LLM Provider ──────────────────────────────────────
LLM_PROVIDER=ollama          # ollama | gemini | openai
USE_LLM=true                 # false = use static fallback data (no LLM needed)

# ── Ollama (local, recommended) ───────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b       # 3.3 GB — good balance of speed and quality
                             # alternatives: llama3:8b, deepseek-r1:8b

# ── Google Gemini (cloud) ─────────────────────────────
GEMINI_API_KEY=your_key_here

# ── OpenAI (cloud) ────────────────────────────────────
OPENAI_API_KEY=your_key_here
```

**Switching providers:** Change `LLM_PROVIDER` and restart — no code changes required.

**Recommended models by use case:**

| Use Case | Provider | Model |
|---|---|---|
| Local / private | Ollama | `gemma3:4b` |
| Fast cloud | Gemini | `gemini-2.5-flash` |
| High-quality cloud | OpenAI | `gpt-4o-mini` |

---

## API Reference

### `POST /run`

Submit a new query and start the pipeline.

**Request:**
```json
{ "query": "Compare SQL vs NoSQL databases" }
```

**Response:**
```json
{
  "id": "3f8a1c2d-...",
  "status": "planning",
  "query": "Compare SQL vs NoSQL databases",
  "steps": [],
  "result": null,
  "metrics": null
}
```

---

### `GET /task/{id}`

Poll for the current state of a running or completed task.

**Response (completed):**
```json
{
  "id": "3f8a1c2d-...",
  "status": "done",
  "query": "Compare SQL vs NoSQL databases",
  "steps": [
    {
      "agent": "planner",
      "subtask": null,
      "output": ["SQL architecture", "NoSQL types", "Scalability comparison"],
      "timestamp": "2026-03-05T10:00:00",
      "duration_ms": 6200
    },
    {
      "agent": "researcher",
      "subtask": "SQL architecture",
      "output": "• SQL uses structured schemas...",
      "timestamp": "2026-03-05T10:00:06",
      "duration_ms": 18400
    }
  ],
  "result": "## SQL Architecture\n\n...",
  "total_duration_ms": 74300,
  "metrics": {
    "llm_calls": 5,
    "retries": 0,
    "duration_ms": 74300
  }
}
```

---

### `GET /health`

```json
{ "status": "ok" }
```

---

## Future Improvements

### Agent Capabilities

- [ ] **Streaming output** — stream Writer tokens to the UI in real time instead of waiting for the full report
- [ ] **Agent memory** — persist summaries across sessions so repeated queries benefit from prior research
- [ ] **Tool use** — equip Research Agents with web search, Wikipedia, or ArXiv API tools for grounded factual retrieval
- [ ] **Dynamic subtask count** — let the Planner decide N based on query complexity instead of a fixed 3

### Performance

- [ ] **Result caching** — cache Research Agent outputs keyed by subtopic so identical subtasks are not re-researched
- [ ] **Streamed review** — run the Reviewer on streaming Writer output to overlap work
- [ ] **Model routing** — route simple tasks to faster/cheaper models and complex tasks to larger ones automatically

### Infrastructure

- [ ] **Persistent task store** — replace the in-memory dict with Redis or PostgreSQL for multi-instance deployments
- [ ] **WebSocket updates** — replace polling with a WebSocket push for lower-latency UI updates
- [ ] **Docker Compose** — containerise backend, frontend, and Ollama for one-command startup
- [ ] **Authentication** — add API key or OAuth2 protection for the `/run` endpoint

### Observability

- [ ] **Distributed tracing** — integrate OpenTelemetry spans across all agents
- [ ] **Structured logging** — emit JSON logs for ingestion into Grafana/Loki
- [ ] **Cost tracking** — record estimated token cost per task for cloud providers

---

## License

MIT — see [LICENSE](LICENSE) for details.

   - [Backend](#backend)
   - [Frontend](#frontend)
3. [Agent Pipeline](#agent-pipeline)
4. [Performance Improvements](#performance-improvements)
5. [Observability Upgrades](#observability-upgrades)
6. [Frontend Redesign](#frontend-redesign)
7. [LLM Provider Configuration](#llm-provider-configuration)
8. [Running the System](#running-the-system)
9. [Project Structure](#project-structure)
10. [Environment Variables](#environment-variables)

---

## System Overview

```
User Query
    │
    ▼
┌─────────────┐     ┌──────────────────────────────────────────┐
│  React UI   │────▶│  FastAPI Backend (port 8001)             │
│  Vite 3000  │◀────│  Planner → Researcher → Writer → Reviewer│
└─────────────┘     └──────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  Ollama (local)     │
                              │  gemma3:4b          │
                              │  port 11434         │
                              └─────────────────────┘
```

The frontend communicates with the backend exclusively through **Vite's dev-server proxy**, which eliminates CORS preflight entirely. All `/run`, `/task/*`, and `/health` requests are forwarded from port 3000 to port 8001 server-side.

---

## Architecture

### Backend

```
backend/
├── main.py                  # FastAPI app, CORS config, .env loader
├── config.py                # USE_LLM flag
├── requirements.txt
├── agents/
│   ├── base_agent.py        # Abstract Agent base class
│   ├── planner_agent.py     # Breaks query → 3 subtasks (JSON array)
│   ├── researcher_agent.py  # Parallel research per subtask
│   ├── writer_agent.py      # Synthesises research into Markdown report
│   └── reviewer_agent.py    # Quality gate: APPROVED or REVISION: <feedback>
├── orchestrator/
│   └── orchestrator.py      # Wires all agents, tracks status, emits Steps
├── llm/
│   └── llm_client.py        # Single async generate() with retry + metrics
├── models/
│   ├── task.py              # Task + Step Pydantic models
│   └── agent_result.py      # AgentResult model
├── api/
│   └── routes.py            # POST /run, GET /task/{id}, GET /health
└── storage/
    └── task_store.py        # In-memory task store (dict)
```

**Key design decisions:**

| Decision | Reason |
|---|---|
| Single `generate()` entry-point in `llm_client.py` | All agents share retry logic, metrics, and provider-switching with zero duplication |
| Async all the way (`asyncio`) | Research subtasks run concurrently without blocking threads |
| Pydantic models for `Task` and `Step` | Auto-validated JSON serialisation for the polling API |
| In-memory task store | Simplicity for local use; swap `task_store.py` for Redis/Postgres without touching agents |

### Frontend

```
frontend/src/
├── App.jsx
├── main.jsx
├── index.css                # Keyframe animations, shimmer, custom scrollbar
├── pages/
│   └── Dashboard.jsx        # Hero landing mode + active task layout
├── components/
│   ├── TaskInput.jsx        # Glass-style dark hero input
│   ├── PipelineVisualizer.jsx  # Per-agent color themes, pulsing ring on active
│   ├── Timeline.jsx         # Expandable step cards with subtask labels
│   ├── ReportViewer.jsx     # Markdown renderer, word count, download button
│   ├── MetricsCard.jsx      # LLM Calls / Retries / Duration stat cards
│   └── StatusBadge.jsx      # Dark-mode translucent status pills
├── hooks/
│   └── useTaskPolling.js    # Polls GET /task/{id} every second
└── services/
    └── api.js               # Axios instance with baseURL: '' (Vite proxy)
```

---

## Agent Pipeline

```
POST /run  {"query": "..."}
      │
      ▼
  [Planner]  ──────────────────────────────── max_tokens=150
      │  Returns: ["subtask A", "subtask B", "subtask C"]
      │
      ▼
  [Researcher × 3]  ──────────────────────── max_tokens=400 each
      │  asyncio.gather() — all 3 run in parallel
      │  Semaphore(3) caps concurrent Ollama connections
      │  Each step stored with subtask label in timeline
      │
      ▼
  [Writer]  ──────────────────────────────── max_tokens=900
      │  Synthesises 3 research outputs into Markdown report
      │  ## headings per topic, short intro, brief conclusion
      │
      ▼
  [Reviewer]  ─────────────────────────────── max_tokens=150
      │  Returns APPROVED  ──────────────────────────────┐
      │  or REVISION: <feedback>                         │
      │        │                                         │
      │        └── re-runs Writer with feedback ─────────┘
      │
      ▼
  Task status = "done", result = final Markdown report
```

**Status transitions visible in the UI:**
`planning` → `researching` → `writing` → `reviewing` → `done`

---

## Performance Improvements

This section documents every optimisation applied to bring end-to-end pipeline time from **4+ minutes** down to approximately **60–90 seconds** on a mid-range CPU running Ollama locally.

### 1. Model Selection

| Before | After | Speedup |
|---|---|---|
| `llama3:8b` (4.7 GB, slow on CPU) | `gemma3:4b` (3.3 GB, faster architecture) | ~40% faster per call |

`gemma3:4b` uses a more efficient attention architecture that is noticeably faster for short-to-medium outputs on CPU-only inference. Configure via `.env`:

```env
OLLAMA_MODEL=gemma3:4b
```

### 2. Per-Agent Token Budgets (`max_tokens`)

The single biggest source of latency was Ollama generating far more tokens than needed because no limit was enforced. Every extra token is linear extra time on CPU inference.

**Before:** All agents called `generate(prompt)` — Ollama defaulted to its model's full context window (~8 000+ tokens possible).

**After:** `generate()` accepts a `max_tokens` parameter, and each agent passes a budget appropriate to its task:

| Agent | max_tokens | Rationale |
|---|---|---|
| Planner | `150` | Only needs a 3-element JSON array — fits in ~60 tokens |
| Researcher | `400` | 3 concise bullet points per subtask |
| Writer | `900` | Full Markdown report, but concise |
| Reviewer | `150` | Only needs `APPROVED` or `REVISION: <one sentence>` |

**Implementation in `llm_client.py`:**

```python
async def generate(prompt: str, max_tokens: int = 600) -> str:
    ...
    return await _generate_ollama(prompt, max_tokens)

async def _generate_ollama(prompt: str, max_tokens: int = 600) -> str:
    json={
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,   # ← enforced per-call
    }
```

### 3. Reduced Subtask Count (Planner)

**Before:** Planner asked for "exactly 4 to 5 research subtasks", capped at `[:5]`.

**After:** Planner asks for exactly **3 subtasks**, capped at `[:3]`.

This cuts the research phase from 4–5 serial LLM calls (when semaphore was limiting concurrency) to 3 fully-parallel calls. Because the 3 calls now run simultaneously under `asyncio.gather`, the research phase takes the time of *one* researcher call rather than multiple.

```python
# planner_agent.py
prompt = (
    "Break the following task into exactly 3 research subtasks. "
    "Return ONLY a JSON array of 3 short strings, no explanation.\n"
    f"Task: {input_data}"
)
response = await generate(prompt, max_tokens=150)
subtasks = subtasks[:3]
```

### 4. Raised Research Concurrency (Semaphore)

**Before:** `asyncio.Semaphore(2)` — only 2 of 5 researchers ran at once; 3 waited.

**After:** `asyncio.Semaphore(3)` — all 3 researchers run simultaneously.

```python
# researcher_agent.py
research_semaphore = asyncio.Semaphore(3)
```

With 3 subtasks and a semaphore of 3, `asyncio.gather()` fires all requests to Ollama at once. While Ollama processes them sequentially internally (single GPU/CPU thread), the total wall-clock time for research equals roughly one researcher call.

### 5. Shorter, Focused Prompts

Long verbose prompts waste tokens on instructions the model doesn't need. Each prompt was trimmed to only what the agent must produce:

**Researcher (before):**
```
"Provide detailed research notes about the following topic.
Return 5-6 well-explained bullet points covering key facts, context, and nuances."
```

**Researcher (after):**
```
"Topic: {subtask}

Give 3 concise bullet points of key facts. Be brief."
```

**Writer (before):**
```
"Write a comprehensive, fully-detailed report...
Each section must be thorough — multiple paragraphs... Do NOT summarize briefly..."
```

**Writer (after):**
```
"Write a clear Markdown report answering the request.
Use ## headings for each topic, a short intro, and a brief conclusion.
Be informative but concise."
```

**Reviewer (before):** No token limit — could generate verbose feedback paragraphs.

**Reviewer (after):** `max_tokens=150` — forces a one-line verdict.

### 6. Retry + Exponential Back-off

Built-in resilience prevents a single transient Ollama error from failing the whole pipeline:

```
Attempt 1 fails → wait 3 s → Attempt 2
Attempt 2 fails → wait 6 s → Attempt 3
Attempt 3 fails → raise exception
```

HTTP 429 rate-limit responses are detected and logged separately.

### 7. Timing Summary

| Phase | Before | After |
|---|---|---|
| Planner | ~38 s (no token cap) | ~5–8 s |
| Research (3 subtasks, parallel) | ~3 × 40 s = 120 s | ~15–25 s |
| Writer | ~60 s (unbounded output) | ~25–35 s |
| Reviewer | ~20 s (verbose) | ~5–8 s |
| **Total** | **~4+ minutes** | **~60–90 seconds** |

---

## Observability Upgrades

### Execution Metrics

Each completed task records how many LLM calls were made, how many retries occurred, and the total wall-clock duration:

```json
{
  "id": "abc-123",
  "status": "done",
  "metrics": {
    "llm_calls": 5,
    "retries": 0,
    "duration_ms": 74200
  }
}
```

Displayed in the UI as three coloured stat cards (LLM Calls / Retries / Duration).

### Structured Timeline Steps

Every agent action is stored as a `Step` object with full metadata:

```python
class Step(BaseModel):
    agent: str               # "planner" | "researcher" | "writer" | "reviewer"
    subtask: Optional[str]   # e.g. "History of microservices" for researcher steps
    output: Any              # raw output or summary
    timestamp: datetime      # when the step started
    duration_ms: Optional[float]  # how long it took
```

The `subtask` field means the Timeline in the UI shows `"Researcher — History of microservices"` rather than a generic "researcher" label.

### Live Status Updates

The orchestrator calls `save_task(task)` after every status transition, so the frontend polling loop always reflects the real current stage:

```
planning → researching → writing → reviewing → done
```

### Reviewer Quality Gate

The Reviewer Agent enforces five checks before approving a draft:

- Factual inconsistencies
- Contradictory dates or numbers
- Logical errors
- Missing sections
- Structural clarity

It returns either `APPROVED` or `REVISION: <specific feedback>`. If a revision is requested, the Writer re-runs with the feedback appended to its prompt. The loop is safeguarded so it cannot run more than a fixed number of times.

---

## Frontend Redesign

The UI was rebuilt from scratch with a dark, glass-morphism aesthetic:

| Component | What it does |
|---|---|
| `Dashboard.jsx` | Two-mode layout: dark hero landing page, then a sticky-header task view once a query is submitted |
| `TaskInput.jsx` | Glass-style dark input with autofocus and an `initialQuery` prop for pre-population |
| `PipelineVisualizer.jsx` | Shows all four pipeline stages with per-agent colour themes; pulsing ring on active stage, checkmark SVG when done |
| `Timeline.jsx` | Expandable step cards with coloured left borders; researcher steps show `"Researcher — {subtask}"` label; shimmer skeleton while loading |
| `ReportViewer.jsx` | Renders Markdown with `react-markdown`; shows word count badge; download-as-`.md` button |
| `MetricsCard.jsx` | Three coloured stat cards for LLM Calls, Retries, and Duration |
| `StatusBadge.jsx` | Dark-mode translucent pill for each pipeline status |
| `index.css` | Keyframe animations (`slide-up`, `fade-in`, `shimmer`, `gradient-x`), custom scrollbar, `.report-prose` typography |

---

## LLM Provider Configuration

Set `LLM_PROVIDER` in `backend/.env` to switch providers without touching code:

| Provider | Config Required |
|---|---|
| `ollama` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` (e.g. `gemma3:4b`) |
| `gemini` | `GEMINI_API_KEY` |
| `openai` | `OPENAI_API_KEY` |

All providers flow through the same `generate(prompt, max_tokens)` interface.

---

## Running the System

### Prerequisites

- Python 3.11+, Node 18+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- Model pulled: `ollama pull gemma3:4b`

### Backend

```powershell
cd multi-agent-system/backend
$env:PYTHONPATH = (Get-Location).Path
& "..\..\venv\Scripts\uvicorn.exe" main:app --port 8001 --reload
```

### Frontend

```powershell
cd multi-agent-system/frontend
npm install
npm run dev          # starts on http://localhost:3000
```

Open `http://localhost:3000` — the Vite proxy forwards API calls to `http://localhost:8001`.

### Health Check

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

---

## Project Structure

```
multi-agent-system/
├── README.md
├── backend/
│   ├── .env                    # LLM credentials and config (not committed)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── planner_agent.py    # max_tokens=150, 3 subtasks
│   │   ├── researcher_agent.py # max_tokens=400, Semaphore(3)
│   │   ├── writer_agent.py     # max_tokens=900
│   │   └── reviewer_agent.py   # max_tokens=150, quality gate
│   ├── llm/
│   │   └── llm_client.py       # generate(prompt, max_tokens), retry, metrics
│   ├── models/
│   │   ├── task.py             # Task + Step (with subtask, duration_ms)
│   │   └── agent_result.py
│   ├── orchestrator/
│   │   └── orchestrator.py     # Pipeline wiring + live status saves
│   ├── api/
│   │   └── routes.py
│   └── storage/
│       └── task_store.py
└── frontend/
    ├── package.json
    ├── vite.config.js           # Proxy: /run, /task, /health → :8001
    ├── tailwind.config.js
    └── src/
        ├── App.jsx
        ├── index.css
        ├── pages/Dashboard.jsx
        ├── components/
        │   ├── TaskInput.jsx
        │   ├── PipelineVisualizer.jsx
        │   ├── Timeline.jsx
        │   ├── ReportViewer.jsx
        │   ├── MetricsCard.jsx
        │   └── StatusBadge.jsx
        ├── hooks/useTaskPolling.js
        └── services/api.js      # baseURL: '' (uses Vite proxy)
```

---

## Environment Variables

```env
# backend/.env

LLM_PROVIDER=ollama          # ollama | gemini | openai
USE_LLM=true

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b       # recommended: fast 3.3 GB model

# Cloud fallbacks
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```
