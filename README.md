# 🤖 Multi-Agent Research System

> A production-grade, async-first agentic pipeline that decomposes any research query into subtasks, executes them in parallel, synthesises a structured report, and validates it — all in a single HTTP call.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![AsyncIO](https://img.shields.io/badge/AsyncIO-native-4CAF50?style=flat)](https://docs.python.org/3/library/asyncio.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Agentic System Architecture](#2-agentic-system-architecture)
3. [Agent Responsibilities](#3-agent-responsibilities)
4. [Orchestrator Design](#4-orchestrator-design)
5. [Parallel Processing Strategy](#5-parallel-processing-strategy)
6. [Low Latency Optimisations](#6-low-latency-optimisations)
7. [Execution Timeline System](#7-execution-timeline-system)
8. [Data Models and State Management](#8-data-models-and-state-management)
9. [Frontend Interaction](#9-frontend-interaction)
10. [Design Principles](#10-design-principles)
11. [Example Execution Flow](#11-example-execution-flow)
12. [Future Improvements](#12-future-improvements)
13. [Technical Stack](#13-technical-stack)
14. [Getting Started](#14-getting-started)
15. [Conclusion](#15-conclusion)

---

## 1. Project Overview

### The Problem

Complex research questions cannot be answered well by a single LLM call. A monolithic prompt approach suffers from:

- **Shallow coverage** — the model cannot go deep on every sub-dimension of a topic within one context window.
- **No quality control** — there is no feedback loop to catch errors, gaps, or contradictions.
- **Zero observability** — you cannot tell _which part_ of the reasoning was slow or wrong.
- **Poor scalability** — sequential calls stack latency linearly.

### The Solution

This project implements a **multi-agent research pipeline** where four specialised AI agents collaborate in a structured workflow:

```
User Query → [Planner] → [Researcher × N] → [Writer] → [Reviewer] → Final Report
                          (parallel)
```

Each agent has a **single, well-defined responsibility**. The **Orchestrator** coordinates their execution, tracks state, measures performance, and surfaces the entire pipeline in a live React dashboard. The result is a validated, structured Markdown report generated from parallel, concurrent research — not a single monolithic prompt.

### What Makes This System Different

| Approach | Latency | Quality Control | Observability | Concurrency |
|---|---|---|---|---|
| Single LLM call | Moderate | None | None | None |
| Sequential agents | High | Partial | Partial | None |
| **This system** | **Low** | **Full review loop** | **Full timeline** | **Parallel research** |

---

## 2. Agentic System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (React / Vite)                   │
│  ┌──────────────┐  POST /run  ┌────────────────────────────────────┐   │
│  │  TaskInput   │ ──────────► │         FastAPI Backend             │   │
│  └──────────────┘             │                                    │   │
│  ┌──────────────┐  GET /task  │  ┌──────────────────────────────┐  │   │
│  │ useTaskPoll  │ ◄────────── │  │        Orchestrator           │  │   │
│  └──────────────┘             │  │                              │  │   │
│  ┌──────────────┐             │  │  ┌──────────┐                │  │   │
│  │  Pipeline    │             │  │  │  Planner │                │  │   │
│  │  Visualizer  │             │  │  └────┬─────┘                │  │   │
│  └──────────────┘             │  │       │ subtasks[]           │  │   │
│  ┌──────────────┐             │  │  ┌────▼──────────────────┐   │  │   │
│  │   Timeline   │             │  │  │  asyncio.gather()      │   │  │   │
│  └──────────────┘             │  │  │  Researcher Researcher  │   │  │   │
│  ┌──────────────┐             │  │  │  Researcher            │   │  │   │
│  │ ReportViewer │             │  │  └────────────┬───────────┘   │  │   │
│  └──────────────┘             │  │               │ research[]    │  │   │
│  ┌──────────────┐             │  │  ┌────────────▼──────┐        │  │   │
│  │ MetricsCard  │             │  │  │      Writer        │        │  │   │
│  └──────────────┘             │  │  └────────────┬───────┘        │  │   │
└─────────────────────────────────  │               │ draft          │  │   │
                               │  │  ┌────────────▼──────┐        │  │   │
                               │  │  │     Reviewer       │        │  │   │
                               │  │  │  (loop ≤ 3 times)  │        │  │   │
                               │  │  └────────────┬───────┘        │  │   │
                               │  │               │ approved        │  │   │
                               │  │  ┌────────────▼──────┐        │  │   │
                               │  │  │  Task Store (RAM)  │        │  │   │
                               │  │  └───────────────────┘        │  │   │
                               │  └──────────────────────────────┘  │   │
                               └─────────────────────────────────────┘   │
                                                                         │
                               ┌──────────────────────────────────────┐  │
                               │         LLM Client (llm_client.py)    │  │
                               │  Gemini │ OpenAI │ Ollama (local)      │  │
                               │  Shared httpx.AsyncClient              │  │
                               │  Exponential backoff (3s → 6s → 12s)  │  │
                               └──────────────────────────────────────┘  │
```

### Information Flow

1. **User** submits a query via the React frontend → `POST /run`
2. **API layer** creates a `Task` object, persists it in the in-memory store, and fires `asyncio.create_task()` — returning immediately (non-blocking)
3. **Orchestrator** takes ownership of the task and drives all agents in sequence
4. **Frontend** polls `GET /task/{id}` every 1.5 seconds, updating the UI as the `status` field transitions
5. On completion, the final `result` (a Markdown report) and `metrics` object are returned in the same polling response

---

## 3. Agent Responsibilities

All agents share a common abstract base class, enforcing a clean `name` / `run()` contract.

```python
# backend/agents/base_agent.py
class Agent(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def run(self, input_data): ...
```

This ABC guarantees that every agent is:
- **Async** — non-blocking, compatible with `asyncio.gather()`
- **Identified** — the `name` property is used for step logging and timeline labelling
- **Replaceable** — swapping implementations requires only changing the class, not the orchestrator

---

### 3.1 Planner Agent

**File:** `backend/agents/planner_agent.py`

The Planner is the entry point for every pipeline run. Its job is **task decomposition**: transforming a broad user query into exactly 3 focused research subtopics.

#### How It Works

```
Input:  "Compare microservices vs monoliths"

Prompt: Task: Compare microservices vs monoliths
        Return ONLY a JSON array of exactly 3 short research subtopic strings.
        No explanation. No markdown.
        Example: ["subtopic 1", "subtopic 2", "subtopic 3"]

Output: ["definition of microservices",
         "definition of monoliths",
         "advantages vs disadvantages"]
```

#### Key Engineering Decisions

| Decision | Rationale |
|---|---|
| **`max_tokens=100`** | The output is a tiny JSON array — capping tokens prevents bloat and speeds up the call dramatically |
| **JSON array extraction via `find("[")` / `rfind("]")`** | LLMs sometimes wrap output in markdown fences; slicing to the first `[` and last `]` is a robust parse-anywhere strategy |
| **Hard cap at 3 subtopics** (`subtasks[:3]`) | Keeps the research fan-out bounded and predictable regardless of what the LLM returns |
| **Fallback subtasks** | If LLM fails entirely, hardcoded fallback subtopics keep the pipeline running — the system never crashes on a planner failure |

#### Fallback Mode (`USE_LLM=false`)

Returns hardcoded subtopics for local testing without any API key:

```python
_FALLBACK_SUBTASKS = [
    "definition of microservices",
    "definition of monoliths",
    "advantages vs disadvantages",
]
```

---

### 3.2 Researcher Agent

**File:** `backend/agents/researcher_agent.py`

The Researcher is the most concurrent part of the pipeline. One researcher instance runs **per subtopic**, all fired simultaneously via `asyncio.gather()`. Each collects exactly 3 verified facts about its assigned subtopic.

#### How It Works

```
Input:  "definition of microservices"

Prompt: Return a JSON object for this topic: "definition of microservices"
        Required format (no markdown, no extra text):
        {"topic": "<topic>", "facts": ["fact1", "fact2", "fact3"]}
        Rules:
        - Exactly 3 facts
        - Each fact: one concise sentence, verified and certain
        - No speculation or invented details

Output: {
          "topic": "definition of microservices",
          "facts": [
            "Microservices is an architectural style...",
            "Each service runs in its own process...",
            "Services communicate via lightweight APIs..."
          ]
        }
```

#### Concurrency Limiting with Semaphore

```python
_semaphore = asyncio.Semaphore(3)

async def run(self, subtask: str) -> AgentResult:
    async with _semaphore:
        ...
```

A **global asyncio Semaphore** caps concurrent LLM calls at 3. This is critical for:
- **Free-tier API rate limits** — prevent 429 errors by controlling throughput
- **Local Ollama servers** — avoid overwhelming VRAM with concurrent inference
- **Predictable performance** — concurrency remains stable regardless of how many subtopics are generated

#### Key Engineering Decisions

| Decision | Rationale |
|---|---|
| **Structured JSON output** | Facts are machine-readable for the writer — no regex parsing of prose needed |
| **`max_tokens=250`** | Enough for 3 sentences; prevents the LLM from rambling |
| **`_parse_research()` key normalisation** | Handles LLM variants (`"key_points"` vs `"facts"`) gracefully |
| **Per-agent fallback** | A single researcher failure does not abort the whole pipeline |

---

### 3.3 Writer Agent

**File:** `backend/agents/writer_agent.py`

The Writer receives the structured research output from all Researcher agents and synthesises it into a coherent, structured Markdown report.

#### How It Works

The `_format_research()` helper converts structured research dicts into a prompt-ready text block:

```python
def _format_research(research_outputs: list) -> str:
    for item in research_outputs:
        topic = item.get("topic", "")
        facts = item.get("facts", [])
        bullet_facts = "\n".join(f"- {f}" for f in facts)
        sections.append(f"### {topic}\n{bullet_facts}")
    return "\n\n".join(sections)
```

This produces a clean, structured text like:

```
### definition of microservices
- Microservices is an architectural style...
- Each service runs in its own process...

### advantages vs disadvantages
- Microservices offer independent deployability...
```

Which is then injected into a tight writer prompt:

```
Request: Compare microservices vs monoliths

Research:
### definition of microservices
- ...

Write a Markdown report using ONLY the facts above.
Format: one-sentence intro, ## heading per topic, bullet facts, one-sentence conclusion.
Max 150 words. No extra commentary.
```

#### Key Engineering Decisions

| Decision | Rationale |
|---|---|
| **"ONLY the facts above"** directive | Prevents hallucination by grounding the writer strictly to researcher-provided data |
| **Explicit Markdown format instructions** | Eliminates unpredictable output structure; the report is immediately renderable |
| **150 word cap** | Keeps reports concise; avoids token bloat that inflates cost and latency |
| **`max_tokens=500`** | Writer gets more budget than planner/reviewer due to content generation demands |
| **Handles both dict and string research inputs** | Makes the agent resilient if a researcher returns a raw string fallback |

---

### 3.4 Reviewer Agent

**File:** `backend/agents/reviewer_agent.py`

The Reviewer is the quality-control gate. It reads the draft report and outputs one of two structured verdicts:

```
APPROVED
  or
REVISION_NEEDED: <issue1>; <issue2>
```

#### How It Works

```python
prompt = (
    "Review this report. Default to APPROVED.\n"
    "Only flag a revision if there is a clear factual contradiction "
    "or an obviously missing required section.\n\n"
    "Return EXACTLY one of:\n"
    "  APPROVED\n"
    "  REVISION_NEEDED: <issue1>; <issue2>\n\n"
    "No other text.\n\n"
    f"Report:\n{draft}"
)
response = (await generate(prompt, max_tokens=80)).strip()
```

#### State Machine Logic

```
Reviewer Response
      │
      ├── starts with "APPROVED"       → AgentResult(status="approved")
      │                                   Orchestrator exits review loop
      │
      ├── starts with "REVISION_NEEDED" → AgentResult(status="revision_needed")
      │                                    Orchestrator calls Writer again
      │                                    (capped at MAX_REVISIONS = 3)
      │
      └── ambiguous / error            → AgentResult(status="approved")
                                         Fail-open to prevent infinite loops
```

#### Key Engineering Decisions

| Decision | Rationale |
|---|---|
| **"Default to APPROVED"** instruction | The reviewer is conservative by design — only flags clear issues, not stylistic ones |
| **`max_tokens=80`** | The verdict is one line; 80 tokens is more than enough and costs almost nothing |
| **Max 3 revisions** (`MAX_REVISIONS = 3`) | Prevents unbounded loops; the system converges to a final report within a known step budget |
| **Fail-open on ambiguity** | Ambiguous LLM responses default to `approved` — the last draft is always used rather than crashing |
| **Feedback stored in `Step.metadata`** | Revision issues are captured in the timeline for full observability |

---

## 4. Orchestrator Design

**File:** `backend/orchestrator/orchestrator.py`

The Orchestrator is the **brain of the system**. It owns the entire pipeline lifecycle: instantiating agents, coordinating execution including timing every step, managing state transitions, and persisting the task at each phase boundary.

### Class Design

```python
class Orchestrator:
    def __init__(self):
        self.planner    = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer     = WriterAgent()
        self.reviewer   = ReviewerAgent()

    def create_task(self, query: str) -> Task:
        task = Task(id=str(uuid.uuid4()), query=query, status="planning", ...)
        save_task(task)
        return task

    async def run(self, task_id: str) -> Task:
        ...
```

Agents are **instantiated once** at startup and reused across all requests. This avoids repeated object construction overhead.

### Task Status State Machine

```
                  ┌──────────────────────────────────┐
                  ▼                                  │
            [planning]                               │
                  │ Planner completes                │
                  ▼                                  │
           [researching]                             │
                  │ All researchers complete          │
                  ▼                                  │
             [writing]  ◄─────────────────┐          │
                  │                       │ revision  │
                  ▼                       │ needed    │
            [reviewing] ──────────────────┘          │
                  │ approved (or max revisions hit)   │
                  ▼                                  │
           [completed] ─────────────────────────────┘
```

Every transition calls `save_task(task)` immediately, so the frontend polling loop always sees an up-to-date status.

### Timing Every Step with `_timed()`

```python
async def _timed(coro):
    t0 = datetime.now()
    result = await coro
    return result, t0, (datetime.now() - t0).total_seconds() * 1000
```

This utility wraps any coroutine and captures:
- **`result`** — the actual agent output
- **`t0`** — the wall-clock start time (stored in the `Step`)
- **`elapsed_ms`** — precise duration in milliseconds

Every agent call is wrapped in `_timed()`, making performance measurement automatic and zero-intrusion.

### Metrics Accounting

```python
metrics_before = get_metrics()
# ... pipeline runs ...
metrics_after = get_metrics()

task.metrics = {
    "llm_calls": metrics_after["llm_calls"] - metrics_before["llm_calls"],
    "retries":   metrics_after["retries"]   - metrics_before["retries"],
    "duration_ms": round(task.total_duration_ms, 2),
}
```

By snapshotting the global counters **before** and **after** the pipeline, metrics are scoped precisely per-task — even under concurrent requests.

### Why the Orchestrator is Critical

In agentic systems, agent logic and coordination logic must be **strictly separated**. Without a dedicated orchestrator:
- Agents would need to know about each other (tight coupling)
- State transitions would be scattered across agent implementations
- Adding new agents would require modifyin existing ones
- Observability would require invasive code changes

The Orchestrator is the **single source of truth** for pipeline control flow. Agents remain dumb, focused, and composable.

---

## 5. Parallel Processing Strategy

### The Core Insight

The three research subtopics are **fully independent** — researching "definition of microservices" does not require the results from "advantages vs disadvantages". This is the key insight that makes parallel execution safe and beneficial.

### Implementation

```python
# backend/orchestrator/orchestrator.py

timed_results = await asyncio.gather(
    *[_timed(self.researcher.run(s)) for s in subtasks]
)
```

`asyncio.gather()` fires all researcher coroutines simultaneously and waits for all of them to complete. With 3 subtopics this turns:

```
Sequential:  [Researcher 1] → [Researcher 2] → [Researcher 3]
             ←───── 3 × T_research ─────────────────────────►

Parallel:    [Researcher 1] ─────────────────────────────────►
             [Researcher 2] ─────────────────────────────────►  ← all at T_research
             [Researcher 3] ─────────────────────────────────►
```

**Latency reduction:** ~66% for the research phase (from 3 × latency to 1 × latency).

### Concurrency Architecture Diagram

```
asyncio event loop
│
├── Task: POST /run handler
│     └── asyncio.create_task(orchestrator.run(task_id))  ← non-blocking!
│
├── Task: orchestrator.run()
│     ├── await planner.run()                   ← sequential (dependency)
│     ├── await asyncio.gather(                 ← PARALLEL
│     │     researcher.run("subtopic_1"),
│     │     researcher.run("subtopic_2"),
│     │     researcher.run("subtopic_3"),
│     │   )
│     ├── await writer.run()                    ← sequential (needs research)
│     └── await reviewer.run()                  ← sequential (needs draft)
│
└── Task: GET /task/{id} (polling)              ← concurrent with above
```

### Semaphore-Controlled Throughput

```python
_semaphore = asyncio.Semaphore(3)

async def run(self, subtask: str) -> AgentResult:
    async with _semaphore:
        ...
```

| Without Semaphore | With Semaphore (limit=3) |
|---|---|
| All N requests hit the API simultaneously | Maximum 3 concurrent API calls |
| Risk of 429 rate limit errors | Smooth throughput, no rate limit bursts |
| Unpredictable latency spikes | Predictable and bounded concurrency |

### Task Dependency Graph

```
                 ┌──────────────┐
                 │    Planner   │
                 └──────┬───────┘
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │Research 1│  │Research 2│  │Research 3│   ← PARALLEL
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         └─────────────┼─────────────┘
                       ▼
                 ┌──────────────┐
                 │    Writer    │
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │   Reviewer   │   ← loop ≤ 3×
                 └──────────────┘
```

---

## 6. Low Latency Optimisations

The system is designed around a core principle: **every millisecond saved at the LLM API boundary is multiplicatively valuable** because agents run in sequence and calls stack.

### 1. Token Budget Engineering

Each agent is given the smallest `max_tokens` value that satisfies its task:

| Agent | `max_tokens` | Rationale |
|---|---|---|
| Planner | `100` | A JSON array of 3 short strings fits easily in ~60 tokens |
| Researcher | `250` | 3 sentences × ~30 words each = ~120 tokens; 250 is safe headroom |
| Writer | `500` | Prose report up to 150 words; needs formatting overhead |
| Reviewer | `80` | One-line verdict; even `REVISION_NEEDED: issue1; issue2` is ~20 tokens |

Tight token budgets reduce:
- **Time to first token** — the model generates less
- **Network payload** — smaller responses transfer faster
- **Cost** — output tokens are charged per token

### 2. Structured Output Contracts

Every agent demands structured output in its prompt:

```
# Planner:
Return ONLY a JSON array. No explanation. No markdown.

# Researcher:
Required format (no markdown, no extra text):
{"topic": "<topic>", "facts": ["fact1", "fact2", "fact3"]}

# Reviewer:
Return EXACTLY one of:
  APPROVED
  REVISION_NEEDED: <issue>
No other text.
```

Structured outputs eliminate the need for post-processing passes, regex extraction on prose, or secondary LLM calls to reformat data.

### 3. Minimal Reasoning Prompts

Prompts instruct the LLM to skip chain-of-thought:
- `"No explanation."` (Planner)
- `"No extra commentary."` (Writer)
- `"No other text."` (Reviewer)

Chain-of-thought increases token count by 3–10×. Suppressing it for deterministic tasks reduces latency proportionally.

### 4. Shared HTTP Client

```python
# backend/llm/llm_client.py
_http = httpx.AsyncClient(timeout=None)
```

A **single `httpx.AsyncClient` instance** is shared across all LLM calls. This means:
- TCP connections are reused (keepalive)
- TLS handshakes happen once per connection
- No per-request DNS resolution overhead

Without connection reuse, each LLM call would pay an additional ~100–300 ms for TCP + TLS setup.

### 5. Non-Blocking API Design

```python
# backend/api/routes.py
@router.post("/run")
async def run_task(request: QueryRequest):
    task = orchestrator.create_task(request.query)
    asyncio.create_task(orchestrator.run(task.id))  # fire-and-forget
    return task                                       # returns immediately
```

The HTTP response returns in < 5 ms with the initial `Task` object. The pipeline runs entirely in the background. The frontend polls for updates rather than waiting on a long-lived HTTP connection. This means:
- No HTTP timeout issues for long-running pipelines
- The server can handle other requests while a pipeline is running
- The UI feels immediately responsive

### 6. Exponential Backoff with Bounded Retries

```python
_MAX_RETRIES = 3
_RETRY_DELAYS = [3, 6, 12]  # seconds

for attempt in range(_MAX_RETRIES):
    try:
        _metrics["llm_calls"] += 1
        return await _generate_...(prompt)
    except Exception as exc:
        await asyncio.sleep(_RETRY_DELAYS[attempt])
```

Retries are bounded at 3 attempts with delays of 3s, 6s, 12s. This prevents:
- Infinite retry storms on persistent API failures
- Cascading 429 rate limit errors from rapid retries

### 7. Parallel Research Execution

As described in Section 5, parallel researcher execution compresses 3 × T_research into 1 × T_research — the single biggest latency saving in the entire pipeline.

---

## 7. Execution Timeline System

### What Is Tracked

Every agent execution is recorded as a `Step` object and appended to the task's `steps` list:

```python
task.steps.append(Step(
    agent=self.planner.name,    # "planner"
    output=planner_result.output,
    timestamp=t0,               # wall-clock start time
    duration_ms=planner_ms,     # milliseconds elapsed
))
```

For researcher steps, the subtask is also stored:

```python
task.steps.append(Step(
    agent=self.researcher.name,
    subtask=subtask,             # e.g. "definition of microservices"
    output=result.output,
    timestamp=t0,
    duration_ms=round(ms, 2),
))
```

The Reviewer step stores feedback in `metadata` when a revision is needed:

```python
task.steps.append(Step(
    agent=self.reviewer.name,
    output=review_result.status,    # "approved" or "revision_needed"
    timestamp=t0,
    duration_ms=review_ms,
    metadata={"feedback": review_result.output} if revision_needed else None,
))
```

### API Endpoints

**`GET /task/{task_id}/timeline`** — returns a structured execution timeline:

```json
{
  "task_id": "abc-123",
  "query": "Compare microservices vs monoliths",
  "status": "completed",
  "start_time": "2024-01-01T10:00:00",
  "end_time":   "2024-01-01T10:00:12",
  "total_duration_ms": 12340.5,
  "timeline": [
    { "step": 1, "agent": "planner",    "duration_ms": 1204.3, "output_preview": "[\"definition of microservices\"...]" },
    { "step": 2, "agent": "researcher", "duration_ms": 3401.2, "output_preview": "{\"topic\": \"definition of microservices\"...}" },
    { "step": 3, "agent": "researcher", "duration_ms": 3201.9, "output_preview": "{\"topic\": \"definition of monoliths\"...}" },
    { "step": 4, "agent": "researcher", "duration_ms": 3188.7, "output_preview": "{\"topic\": \"advantages vs disadvantages\"...}" },
    { "step": 5, "agent": "writer",     "duration_ms": 2901.1, "output_preview": "Draft created" },
    { "step": 6, "agent": "reviewer",   "duration_ms":  412.3, "output_preview": "approved" }
  ]
}
```

**`GET /task/{task_id}/pipeline`** — returns per-agent aggregate stats:

```json
{
  "task_id": "abc-123",
  "total_duration_ms": 12340.5,
  "stages": [
    { "agent": "planner",    "runs": 1, "total_ms": 1204.3 },
    { "agent": "researcher", "runs": 3, "total_ms": 9791.8 },
    { "agent": "writer",     "runs": 1, "total_ms": 2901.1 },
    { "agent": "reviewer",   "runs": 1, "total_ms":  412.3  }
  ]
}
```

### Frontend Timeline Component

The `Timeline` React component renders steps as they arrive via polling:

```
Execution Timeline                                          6 steps

  ● Planner                                    1204 ms    10:00:01
    Planned 3 subtasks: definition of microservices · definition of (...)

  ● Researcher — definition of microservices   3401 ms    10:00:02
    {"topic": "definition of microservices", "facts": [...]}

  ● Researcher — definition of monoliths       3201 ms    10:00:02
    {"topic": "definition of monoliths", ...}

  ● Researcher — advantages vs disadvantages   3188 ms    10:00:02
    {"topic": "advantages vs disadvantages", ...}

  ● Writer                                     2901 ms    10:00:06
    Draft created

  ● Reviewer                                    412 ms    10:00:09
    approved
```

---

## 8. Data Models and State Management

The system uses [Pydantic v2](https://docs.pydantic.dev/) for all data models. Pydantic provides automatic validation, serialisation, and JSON schema generation — essential for a type-safe API.

### `AgentResult`

**File:** `backend/models/agent_result.py`

```python
class AgentResult(BaseModel):
    status: str           # "success" | "approved" | "revision_needed"
    output: Optional[Any] = None    # agent-specific payload
    metadata: Optional[Dict] = None # optional extra data
```

`AgentResult` is the **universal return type** for all agents. By standardising the return contract:
- The orchestrator can handle any agent result uniformly
- Status strings drive control flow decisions (`approved`, `revision_needed`)
- The `output` field carries agent-specific data (list of subtopics, research dict, draft text, verdict)

### `Step`

**File:** `backend/models/task.py`

```python
class Step(BaseModel):
    agent: str                    # agent name ("planner", "researcher", ...)
    subtask: Optional[str] = None # researcher subtopic (if applicable)
    output: Any                   # agent output snapshot
    timestamp: datetime           # wall-clock execution start
    duration_ms: Optional[float]  # execution time in milliseconds
    metadata: Optional[Dict]      # extra data (e.g. reviewer feedback)
```

Each `Step` is an **immutable audit record** of a single agent execution. The ordered list of steps on a `Task` forms the complete execution audit trail.

### `Task`

**File:** `backend/models/task.py`

```python
class Task(BaseModel):
    id: str                              # UUID
    query: str                           # original user query
    status: str                          # current pipeline phase
    steps: List[Step] = []               # ordered execution log
    result: Optional[Any] = None         # final report (when completed)
    start_time: Optional[datetime]       # pipeline start
    end_time: Optional[datetime]         # pipeline end
    total_duration_ms: Optional[float]   # wall-clock pipeline duration
    metrics: Optional[Dict]              # LLM call counts, retries, duration
```

The `Task` object is the **single source of truth** for a pipeline run. It is:
- Returned immediately on `POST /run` (with `status="planning"`)
- Updated in-place as the pipeline progresses
- Read on every `GET /task/{id}` poll
- Never destroyed — useful for post-run analysis

### Task Store

**File:** `backend/storage/task_store.py`

```python
tasks = {}

def save_task(task): tasks[task.id] = task
def get_task(task_id): return tasks.get(task_id)
```

The current implementation uses a **Python in-memory dict**. This is intentionally simple for the initial version — the abstraction (two functions, clear interface) makes it trivially replaceable with Redis, PostgreSQL, or any other persistence layer without touching the orchestrator or API layer.

### Why Structured Models Matter in Agentic Systems

| Without Models | With Pydantic Models |
|---|---|
| Dict keys typo silently at runtime | Type-checked at model creation |
| Pipeline state is implicit | State is explicit and queryable |
| Adding a field touches multiple files | Add to the model once, serialised automatically |
| Debugging requires print statements | Full task/step history survives until inspection |

---

## 9. Frontend Interaction

**Directory:** `frontend/src/`

The frontend is a **React 18 / Vite / Tailwind** single-page application. It interacts with the backend exclusively through a defined API service layer and renders the agent pipeline in real time.

### Architecture

```
src/
├── pages/
│   └── Dashboard.jsx          ← top-level page, owns all state
├── components/
│   ├── TaskInput.jsx           ← query form + submit
│   ├── PipelineVisualizer.jsx  ← 4-stage horizontal flow diagram
│   ├── Timeline.jsx            ← ordered step-by-step log
│   ├── ReportViewer.jsx        ← Markdown report renderer
│   ├── StatusBadge.jsx         ← animated status badge
│   └── MetricsCard.jsx         ← LLM calls / retries / duration
├── hooks/
│   └── useTaskPolling.js       ← auto-polling hook
└── services/
    └── api.js                  ← axios API client (all backend calls)
```

### Polling with `useTaskPolling`

**File:** `frontend/src/hooks/useTaskPolling.js`

```javascript
export function useTaskPolling(taskId) {
  const [task, setTask] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    const poll = async () => {
      const data = await fetchTask(taskId)
      setTask(data)
      if (data.status === 'completed') {
        clearInterval(intervalRef.current)   // auto-stop polling
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1500)  // every 1.5 seconds
    return () => clearInterval(intervalRef.current) // cleanup on unmount
  }, [taskId])

  return { task, error }
}
```

Every 1.5 seconds, the hook fetches the latest task state. When `status === "completed"`, polling stops automatically. This is a clean, self-managing hook with no memory leaks.

### API Service Layer

**File:** `frontend/src/services/api.js`

All backend communication is centralised in a single Axios instance:

```javascript
const api = axios.create({
  baseURL: '',       // relative — proxied by Vite to http://localhost:8001
  timeout: 600000,   // 10 min timeout for local LLM inference
})

export async function submitTask(query)        // POST /run
export async function fetchTask(taskId)        // GET /task/{id}
export async function fetchTimeline(taskId)    // GET /task/{id}/timeline
export async function fetchPipeline(taskId)    // GET /task/{id}/pipeline
```

Using a **relative base URL + Vite dev proxy** means the frontend calls `/run` locally, which Vite transparently forwards to `http://localhost:8001/run`. No CORS issues during development, and production deployment only requires changing the proxy target.

### Pipeline Visualiser

**File:** `frontend/src/components/PipelineVisualizer.jsx`

```
🧠 Planner ──────► 🔍 Researcher ──────► ✍️ Writer ──────► ✅ Reviewer
  (done ✓)           (done ✓)             (active ⟳)          (idle)
```

The visualiser maps pipeline status strings to visual node states:

| Task `status` | Node State Logic |
|---|---|
| `"planning"` | Planner = active, rest = idle |
| `"researching"` | Planner = done, Researcher = active |
| `"writing"` | Planner + Researcher = done, Writer = active |
| `"reviewing"` | Planner + Researcher + Writer = done, Reviewer = active |
| `"completed"` | All = done ✓ |

Active nodes display a **pulsing ring animation** (CSS `animate-ping`). Done nodes show a **green checkmark**. Idle nodes are greyed out. Connector arrows between nodes light up progressively as stages complete.

### Report Viewer

**File:** `frontend/src/components/ReportViewer.jsx`

Renders the final Markdown report using `react-markdown`. Additional features:
- **Copy to clipboard** button with "Copied ✓" feedback
- **Download as `.md` file** via Blob URL
- **Word count + read time** estimate in the header
- **Shimmer skeleton** shown while the report is being generated（`result === null`）

### Status Badge

**File:** `frontend/src/components/StatusBadge.jsx`

Each pipeline status maps to a distinct colour and animated dot:

| Status | Colour | Animation |
|---|---|---|
| `planning` | Blue | Pulsing dot |
| `researching` | Violet | Pulsing dot |
| `writing` | Amber | Pulsing dot |
| `reviewing` | Orange | Pulsing dot |
| `completed` | Emerald | Static dot |
| `error` | Red | Static dot |

---

## 10. Design Principles

### 1. Clean Abstractions

The `Agent` ABC enforces a minimal interface (`name`, `async run()`). The `Orchestrator` never inspects agent internals — it only calls `run()` and reads `AgentResult`. This makes agents independently testable and swappable.

### 2. Separation of Concerns

| Layer | Responsibility |
|---|---|
| `agents/` | LLM prompting, parsing, fallbacks |
| `orchestrator/` | Sequencing, timing, state management |
| `api/` | HTTP routing, request/response shaping |
| `models/` | Data structures, validation |
| `storage/` | Persistence (currently RAM, replaceable) |
| `llm/` | Provider abstraction, retries, metrics |

No layer crosses into another's domain.

### 3. Modular Agent Design

Adding a new agent (e.g. a `FactCheckerAgent`) requires:
1. Create a file in `agents/`
2. Extend `Agent` ABC
3. Add one call site in `orchestrator.py`

No other code changes needed.

### 4. Async-First Architecture

Every blocking operation is `await`-ed. The event loop is never blocked. This means:
- Multiple pipeline requests can run concurrently on a single server process
- Polling requests are served instantly while pipelines execute in the background
- I/O (LLM API calls) yields control, enabling other tasks to progress

### 5. Observable Pipelines

Every agent call is timed, logged, and stored. The backend exposes three levels of observability:
- `GET /task/{id}` — full task state with all steps
- `GET /task/{id}/timeline` — chronological execution log with durations
- `GET /task/{id}/pipeline` — per-agent aggregate performance

The frontend renders all three levels simultaneously.

### 6. Fail-Open Resilience

Every agent has a fallback path:
- **Planner:** returns hardcoded subtopics on LLM failure
- **Researcher:** returns a placeholder research object per subtopic
- **Writer:** returns raw research text as a basic report
- **Reviewer:** defaults to `approved` on ambiguous or failed responses

The pipeline **never crashes** due to a single agent failure. Degraded output is always preferred over a broken pipeline.

### 7. Provider Agnosticism

The `llm_client.py` supports three backends behind a single `generate()` function:

```python
if config.LLM_PROVIDER == "gemini":   return await _generate_gemini(prompt)
if config.LLM_PROVIDER == "ollama":   return await _generate_ollama(prompt, max_tokens)
                                       return await _generate_openai(prompt, max_tokens)
```

Switching providers requires only changing a single environment variable (`LLM_PROVIDER`). No agent code changes.

### 8. Extensibility

The system is designed for extension, not modification:
- New agents → define and wire up, no changes to existing agents
- New providers → add a `_generate_xxx()` function to `llm_client.py`
- New storage → swap out `task_store.py`
- New API endpoints → add to `routes.py`

---

## 11. Example Execution Flow

### Query: `"How does GPT-4 work?"`

```
t=0ms     User submits query via TaskInput component
             POST /run { "query": "How does GPT-4 work?" }

t=3ms     API creates Task { id: "f4a7...", status: "planning" }
          asyncio.create_task(orchestrator.run("f4a7..."))
          API returns immediately → frontend starts polling

t=5ms     [Orchestrator] Pipeline start, snapshot metrics_before
          [Orchestrator] Calls PlannerAgent.run("How does GPT-4 work?")

t=1200ms  [PlannerAgent] LLM responds:
            ["transformer architecture", "training methodology", "RLHF alignment"]
          Step appended: { agent: "planner", duration_ms: 1195, output: [...] }
          task.status → "researching", save_task()

t=1205ms  [Orchestrator] asyncio.gather() fires 3 researchers simultaneously:
            ResearcherAgent.run("transformer architecture")
            ResearcherAgent.run("training methodology")
            ResearcherAgent.run("RLHF alignment")

          ← All 3 run concurrently, each making one LLM call →

t=4800ms  [Researcher × 3] All complete (concurrent, not sequential)
          Steps appended for each:
            { agent: "researcher", subtask: "transformer architecture", duration_ms: 3192 }
            { agent: "researcher", subtask: "training methodology",      duration_ms: 3088 }
            { agent: "researcher", subtask: "RLHF alignment",            duration_ms: 2941 }
          task.status → "writing", save_task()

t=4802ms  [Orchestrator] Calls WriterAgent.run(query, subtasks, research_outputs)
          Writer receives structured research → synthesises Markdown report

t=7500ms  [WriterAgent] Draft completed:
          "# GPT-4: Architecture and Training\n\n## Transformer Architecture\n..."
          Step appended: { agent: "writer", duration_ms: 2698, output: "Draft created" }
          task.status → "reviewing", save_task()

t=7502ms  [ReviewerAgent] Receives draft, sends 80-token verdict prompt

t=7900ms  [ReviewerAgent] Response: "APPROVED"
          Step appended: { agent: "reviewer", duration_ms: 398, output: "approved" }

t=7902ms  [Orchestrator] Review loop exits (approved on first attempt)
          task.status → "completed"
          task.result  = "# GPT-4: Architecture and Training\n\n..."
          task.metrics = { llm_calls: 5, retries: 0, duration_ms: 7902 }
          save_task()

t=9000ms  [Frontend] Polling detects status === "completed"
          useTaskPolling stops interval
          ReportViewer renders the Markdown report
          MetricsCard shows: LLM Calls: 5, Retries: 0, Duration: 7.9s
          PipelineVisualizer: all 4 stages show green ✓
          Timeline: 6 steps displayed with timestamps and durations
```

### Summary of the Execution

| Phase | Time | LLM Calls |
|---|---|---|
| Planning | 1.2s | 1 |
| Research (parallel) | 3.6s (wall clock) | 3 simultaneous |
| Writing | 2.7s | 1 |
| Review | 0.4s | 1 |
| **Total** | **~7.9s** | **6** |

Without parallelism, research alone would take ~9s (3 × 3s). Parallel execution compresses that to ~3.6s — nearly a 60% reduction in total pipeline time.

---

## 12. Future Improvements

### 1. Dynamic DAG Pipelines

Replace the hardcoded linear pipeline with a directed acyclic graph (DAG) scheduler. The orchestrator would accept a pipeline definition like:

```python
pipeline = {
    "planner": [],
    "researcher": ["planner"],
    "fact_checker": ["researcher"],
    "writer": ["fact_checker"],
    "reviewer": ["writer"],
}
```

This enables arbitrary agent topologies, conditional branches, and merge/fan-out nodes without changing orchestrator logic.

### 2. Streaming LLM Outputs

Integrate streaming API responses (Server-Sent Events or WebSocket) to begin rendering the report as the Writer generates it token-by-token, rather than waiting for the complete response.

### 3. Vector Memory for Agents

Give researcher agents access to a vector database (e.g. Pinecone, Chroma) to retrieve relevant context from previous research runs. This would:
- Reduce redundant LLM calls for repeated topics
- Enable retrieval-augmented generation (RAG) workflows
- Allow the system to build a growing knowledge base

### 4. Persistent Task Storage

Replace the in-memory `task_store.py` with a proper persistence layer (Redis for hot tasks, PostgreSQL for archived tasks). This would survive server restarts and enable multi-instance deployments.

### 5. User-Configurable Pipelines

Expose a UI where users can define the pipeline topology — add/remove agents, set concurrency limits, define approval thresholds, and choose which LLM provider each agent uses.

### 6. Agent Plugins

Define an agent plugin interface that allows third-party agents to be installed (e.g. a web search agent using SerpAPI, a code execution agent using a sandboxed Python runtime).

### 7. Streaming Pipeline Events

Replace the polling architecture with WebSocket push events. The backend would stream each step completion event to the frontend the moment it occurs, reducing perceived latency and eliminating polling overhead.

### 8. Multi-Level Reviewer

Add a panel of specialist reviewers (factual accuracy, style, completeness) that independently evaluate the draft. Their verdicts are aggregated with a majority-vote or weighted-score mechanism.

### 9. Evaluation Metrics

Track report quality metrics over time: citation accuracy, completeness score, reading level, sentiment. Use these to automatically tune prompts and evaluate the impact of model changes.

---

## 13. Technical Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.11+ | Core language |
| **FastAPI** | 0.110+ | Async HTTP framework |
| **Uvicorn** | latest | ASGI server |
| **Pydantic v2** | latest | Data validation and serialisation |
| **asyncio** | stdlib | Native concurrency primitives |
| **httpx** | latest | Async HTTP client (shared LLM connection) |
| **python-dotenv** | latest | Environment variable management |
| **google-genai** | latest | Google Gemini SDK |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| **React** | 18 | UI framework |
| **Vite** | 5 | Dev server and bundler |
| **Tailwind CSS** | 3.4 | Utility-first styling |
| **Axios** | 1.6 | HTTP client |
| **react-markdown** | 10 | Markdown report rendering |
| **@tailwindcss/typography** | 0.5 | Prose styling for rendered Markdown |

### LLM Providers (configurable)

| Provider | Model | Deployment |
|---|---|---|
| **Google Gemini** | `gemini-2.5-flash` (default) | Cloud API |
| **OpenAI** | `gpt-4o-mini` (configurable) | Cloud API |
| **Ollama** | `llama3:8b` (configurable) | Local self-hosted |

---

## 14. Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An API key for Gemini, OpenAI, or a local Ollama installation

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd multi-agent-system/backend

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set LLM_PROVIDER and the relevant API key

# 5. Start the backend
uvicorn main:app --reload --port 8001
```

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd multi-agent-system/frontend

# 2. Install dependencies
npm install

# 3. Start the dev server (proxies API to :8001)
npm run dev
```

Visit `http://localhost:5173` in your browser.

### Environment Variables

```env
# .env (backend)

# Enable or disable real LLM calls (set to false for local testing without API key)
USE_LLM=true

# Provider: "gemini", "openai", or "ollama"
LLM_PROVIDER=gemini

# Google Gemini (recommended — fast, free tier available)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# OpenAI (alternative)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Ollama (local, no API key required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

### Project Structure

```
multi-agent-system/
├── backend/
│   ├── main.py                    # FastAPI app + CORS setup
│   ├── config.py                  # Environment-driven configuration
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── base_agent.py          # Abstract Agent ABC
│   │   ├── planner_agent.py       # Task decomposition
│   │   ├── researcher_agent.py    # Parallel fact collection
│   │   ├── writer_agent.py        # Report synthesis
│   │   └── reviewer_agent.py      # Quality gate
│   ├── orchestrator/
│   │   └── orchestrator.py        # Pipeline coordination engine
│   ├── models/
│   │   ├── task.py                # Task + Step Pydantic models
│   │   └── agent_result.py        # AgentResult model
│   ├── api/
│   │   └── routes.py              # REST endpoints
│   ├── llm/
│   │   └── llm_client.py          # Multi-provider LLM client
│   └── storage/
│       └── task_store.py          # In-memory task store
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        ├── pages/
        │   └── Dashboard.jsx      # Top-level page with all state
        ├── components/
        │   ├── TaskInput.jsx       # Query input form
        │   ├── PipelineVisualizer.jsx # Live stage flow diagram
        │   ├── Timeline.jsx        # Step-by-step execution log
        │   ├── ReportViewer.jsx    # Markdown report renderer
        │   ├── StatusBadge.jsx     # Animated status indicator
        │   └── MetricsCard.jsx     # Performance summary
        ├── hooks/
        │   └── useTaskPolling.js   # Auto-polling hook
        └── services/
            └── api.js              # Axios API service layer
```

---

## 15. Conclusion

Agentic architectures represent a fundamental shift in how we design AI systems. Rather than asking a single model to do everything, we decompose complex tasks into **specialised, composable agents** that each do one thing extraordinarily well.

This system demonstrates why this approach is powerful:

**Specialisation beats generalisation.** A planner that only decomposes tasks generates better subtopics than a generalist. A reviewer that only evaluates quality gives sharper feedback than a model switching contexts.

**Parallelism is free performance.** Independent research tasks have no data dependency on each other. Running them concurrently with `asyncio.gather()` is zero additional engineering cost for a ~60% latency improvement.

**Observability enables iteration.** Full step-by-step timing means you can immediately see whether the planner, researcher, writer, or reviewer is the bottleneck — and fix it.

**Structure beats prose.** Agents that return structured JSON rather than free text eliminate downstream parsing complexity, improve reliability, and make data easy to inspect and route.

**Resilience through fallbacks.** Every agent has a fallback path. The system degrades gracefully under API failures rather than crashing. A degraded research pipeline that returns a partial report is infinitely more useful than a 500 error.

The pipeline in this project is intentionally simple — four agents, one linear flow. But the architecture scales naturally to **DAG-based pipelines with dozens of specialist agents**, persistent vector memory, streaming outputs, and user-defined workflows. The foundation is here. The ceiling is the complexity of the problems you want to solve.

---

<div align="center">

Built with Python · FastAPI · AsyncIO · React · Vite

*Planner → Researcher → Writer → Reviewer → Done.*

</div>
