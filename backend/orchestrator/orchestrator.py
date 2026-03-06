"""Orchestrator — coordinates agents through a configurable pipeline.

The pipeline is driven by a PipelineConfig (list of agent names).  Each agent
is dispatched through _execute_stage, which maps the agent's name to the
appropriate execution logic.  The writer-reviewer revision loop is handled
as a first-class pattern: whenever a reviewer agent appears in the pipeline,
the immediately preceding writer agent is used for revision cycles.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from agents.base_agent import Agent
from agents.registry import build_pipeline
from models.pipeline import DEFAULT_PIPELINE, PipelineConfig
from models.task import Step, Task
from storage.task_store import get_task, save_task
from llm.llm_client import get_metrics

log = logging.getLogger(__name__)

MAX_REVISIONS = 3


@dataclass
class PipelineContext:
    """Mutable state threaded through every stage of the pipeline."""
    query: str
    subtasks: List[str] = field(default_factory=list)
    research_outputs: List = field(default_factory=list)
    draft: str = ""


async def _timed(coro):
    """Await *coro* and return (result, start_time, elapsed_ms)."""
    t0 = datetime.now()
    result = await coro
    return result, t0, (datetime.now() - t0).total_seconds() * 1000


class Orchestrator:

    def create_task(
        self,
        query: str,
        pipeline_config: Optional[PipelineConfig] = None,
    ) -> Task:
        """Create, persist, and return a new task in the 'planning' state."""
        agent_names = pipeline_config.agents if pipeline_config else DEFAULT_PIPELINE
        task = Task(
            id=str(uuid.uuid4()),
            query=query,
            status="planning",
            pipeline=agent_names,
            start_time=datetime.now(),
        )
        save_task(task)
        return task

    async def run(
        self,
        task_id: str,
        pipeline_config: Optional[PipelineConfig] = None,
    ) -> Task:
        task = get_task(task_id)
        pipeline_start = datetime.now()
        task.start_time = pipeline_start
        metrics_before = get_metrics()
        save_task(task)

        agent_names = (
            pipeline_config.agents
            if pipeline_config
            else (task.pipeline or DEFAULT_PIPELINE)
        )
        agents = build_pipeline(agent_names)
        context = PipelineContext(query=task.query)

        # Locate the writer to reuse during review-revision cycles.
        writer = next((a for a in agents if a.name == "writer"), None)

        try:
            for agent in agents:
                if agent.name == "reviewer":
                    context = await self._run_review_loop(agent, writer, context, task)
                else:
                    context = await self._execute_stage(agent, context, task)
        except Exception as exc:
            task.status = "error"
            task.metrics = {"error": str(exc)}
            save_task(task)
            raise

        pipeline_end = datetime.now()
        metrics_after = get_metrics()

        task.status = "completed"
        task.result = context.draft or None
        task.end_time = pipeline_end
        task.total_duration_ms = (pipeline_end - pipeline_start).total_seconds() * 1000
        task.metrics = {
            "llm_calls": metrics_after["llm_calls"] - metrics_before["llm_calls"],
            "retries":   metrics_after["retries"]   - metrics_before["retries"],
            "duration_ms": round(task.total_duration_ms, 2),
        }
        save_task(task)
        return task

    # ------------------------------------------------------------------
    # Stage dispatchers
    # ------------------------------------------------------------------

    async def _execute_stage(
        self,
        agent: Agent,
        context: PipelineContext,
        task: Task,
    ) -> PipelineContext:
        name = agent.name
        if name == "planner":
            return await self._run_planner(agent, context, task)
        if name == "researcher":
            return await self._run_researcher(agent, context, task)
        if name == "factchecker":
            return await self._run_factchecker(agent, context, task)
        if name == "writer":
            return await self._run_writer(agent, context, task)
        # Unknown agent — skip with a warning step.
        log.warning("No execution strategy for agent '%s', skipping.", name)
        return context

    # ------------------------------------------------------------------
    # Individual stage implementations
    # ------------------------------------------------------------------

    async def _run_planner(self, agent, context, task):
        result, t0, ms = await _timed(agent.run(context.query))
        task.status = "planning"
        task.steps.append(Step(
            agent=agent.name,
            output=result.output,
            timestamp=t0,
            duration_ms=round(ms, 2),
        ))
        save_task(task)
        subtasks = result.output
        context.subtasks = subtasks if isinstance(subtasks, list) else [str(subtasks)]
        return context

    async def _run_researcher(self, agent, context, task):
        task.status = "researching"
        save_task(task)
        subtasks = context.subtasks or [context.query]
        timed_results = await asyncio.gather(
            *[_timed(agent.run(s)) for s in subtasks]
        )
        for subtask, (result, t0, ms) in zip(subtasks, timed_results):
            context.research_outputs.append(result.output)
            task.steps.append(Step(
                agent=agent.name,
                subtask=subtask,
                output=result.output,
                timestamp=t0,
                duration_ms=round(ms, 2),
            ))
        save_task(task)
        return context

    async def _run_factchecker(self, agent, context, task):
        task.status = "fact_checking"
        save_task(task)
        result, t0, ms = await _timed(agent.run(context.research_outputs))
        task.steps.append(Step(
            agent=agent.name,
            output=f"Fact-checked {len(context.research_outputs)} research item(s)",
            timestamp=t0,
            duration_ms=round(ms, 2),
        ))
        save_task(task)
        if isinstance(result.output, list):
            context.research_outputs = result.output
        return context

    async def _run_writer(self, agent, context, task):
        task.status = "writing"
        save_task(task)
        result, t0, ms = await _timed(
            agent.run(context.query, context.subtasks, context.research_outputs)
        )
        context.draft = result.output
        task.steps.append(Step(
            agent=agent.name,
            output="Draft created",
            timestamp=t0,
            duration_ms=round(ms, 2),
        ))
        save_task(task)
        return context

    async def _run_review_loop(self, reviewer, writer, context, task):
        """Run the reviewer; if revision is needed and a writer is available,
        re-write and re-review up to MAX_REVISIONS times."""
        task.status = "reviewing"
        save_task(task)

        for revision in range(MAX_REVISIONS + 1):
            review_result, t0, ms = await _timed(reviewer.run(context.draft))
            task.steps.append(Step(
                agent=reviewer.name,
                output=review_result.status,
                timestamp=t0,
                duration_ms=round(ms, 2),
                metadata=(
                    {"feedback": review_result.output}
                    if review_result.status == "revision_needed"
                    else None
                ),
            ))

            if review_result.status == "approved":
                break

            if revision == MAX_REVISIONS or writer is None:
                log.warning(
                    "Max revisions (%d) reached or no writer in pipeline — accepting last draft.",
                    MAX_REVISIONS,
                )
                break

            # Revision cycle: rewrite then review again.
            task.status = "writing"
            save_task(task)
            writer_result, t0, ms = await _timed(
                writer.run(context.query, context.subtasks, context.research_outputs)
            )
            context.draft = writer_result.output
            task.steps.append(Step(
                agent=writer.name,
                output="Revised draft created",
                timestamp=t0,
                duration_ms=round(ms, 2),
            ))
            task.status = "reviewing"
            save_task(task)

        return context
