import uuid
import asyncio
from datetime import datetime

from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent

from models.task import Task, Step
from storage.task_store import save_task, get_task
from llm.llm_client import get_metrics

MAX_REVISIONS = 3


async def _timed(coro):
    """Run a coroutine and return (result, start_time, elapsed_ms)."""
    t0 = datetime.now()
    result = await coro
    return result, t0, (datetime.now() - t0).total_seconds() * 1000


class Orchestrator:

    def __init__(self):
        self.planner    = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer     = WriterAgent()
        self.reviewer   = ReviewerAgent()

    def create_task(self, query: str) -> Task:
        """Create, persist, and return a new task in the 'planning' state."""
        task = Task(
            id=str(uuid.uuid4()),
            query=query,
            status="planning",
            start_time=datetime.now(),
        )
        save_task(task)
        return task

    async def run(self, task_id: str) -> Task:
        task = get_task(task_id)
        pipeline_start = datetime.now()
        task.start_time = pipeline_start
        metrics_before = get_metrics()
        save_task(task)

        # ── Planner ─────────────────────────────────────────────
        planner_result, t0, planner_ms = await _timed(self.planner.run(task.query))
        task.steps.append(Step(
            agent=self.planner.name,
            output=planner_result.output,
            timestamp=t0,
            duration_ms=planner_ms,
        ))
        subtasks = planner_result.output

        # ── Research (parallel) ──────────────────────────────────
        task.status = "researching"
        save_task(task)

        timed_results = await asyncio.gather(
            *[_timed(self.researcher.run(s)) for s in subtasks]
        )
        research_outputs = []
        for subtask, (result, t0, ms) in zip(subtasks, timed_results):
            research_outputs.append(result.output)
            task.steps.append(Step(
                agent=self.researcher.name,
                subtask=subtask,
                output=result.output,
                timestamp=t0,
                duration_ms=round(ms, 2),
            ))

        # ── Writer ─────────────────────────────────────────────
        task.status = "writing"
        save_task(task)

        writer_result, t0, writer_ms = await _timed(
            self.writer.run(task.query, subtasks, research_outputs)
        )
        draft = writer_result.output
        task.steps.append(Step(
            agent=self.writer.name,
            output="Draft created",
            timestamp=t0,
            duration_ms=writer_ms,
        ))

        # ── Review loop (capped at MAX_REVISIONS) ───────────────────
        task.status = "reviewing"
        save_task(task)

        for revision in range(MAX_REVISIONS + 1):
            review_result, t0, review_ms = await _timed(self.reviewer.run(draft))
            task.steps.append(Step(
                agent=self.reviewer.name,
                output=review_result.status,
                timestamp=t0,
                duration_ms=review_ms,
                metadata={"feedback": review_result.output} if review_result.status == "revision_needed" else None,
            ))

            if review_result.status == "approved":
                break

            if revision == MAX_REVISIONS:
                print(f"[Orchestrator] Max revisions ({MAX_REVISIONS}) reached, using last draft.")
                break

            task.status = "writing"
            save_task(task)

            writer_result, t0, writer_ms = await _timed(
                self.writer.run(task.query, subtasks, research_outputs)
            )
            draft = writer_result.output
            task.steps.append(Step(
                agent=self.writer.name,
                output="Revised draft created",
                timestamp=t0,
                duration_ms=writer_ms,
            ))

            task.status = "reviewing"
            save_task(task)

        # ── Finalize ───────────────────────────────────────────
        pipeline_end = datetime.now()
        metrics_after = get_metrics()

        task.status = "completed"
        task.result = draft
        task.end_time = pipeline_end
        task.total_duration_ms = (pipeline_end - pipeline_start).total_seconds() * 1000
        task.metrics = {
            "llm_calls": metrics_after["llm_calls"] - metrics_before["llm_calls"],
            "retries":   metrics_after["retries"]   - metrics_before["retries"],
            "duration_ms": round(task.total_duration_ms, 2),
        }
        save_task(task)
        return task