import uuid
import asyncio
from datetime import datetime

from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent

from models.task import Task, Step
from storage.task_store import save_task
from llm.llm_client import get_metrics


class Orchestrator:

    def __init__(self):

        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    async def run(self, query, task_id: str | None = None):

        pipeline_start = datetime.now()
        metrics_before = get_metrics()

        # Re-use a pre-created task (background mode) or create one now
        if task_id:
            from storage.task_store import get_task as _get
            task = _get(task_id)
            task.start_time = pipeline_start
        else:
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                query=query,
                status="planning",
                start_time=pipeline_start,
            )
        # Persist so the polling endpoint can find this task
        save_task(task)

        # Planner
        t0 = datetime.now()
        planner_result = await self.planner.run(query)
        t1 = datetime.now()

        task.steps.append(
            Step(
                agent="planner",
                output=planner_result.output,
                timestamp=t0,
                duration_ms=(t1 - t0).total_seconds() * 1000
            )
        )

        subtasks = planner_result.output

        # Research — all subtasks run in parallel
        task.status = "researching"
        save_task(task)  # live update

        research_start = datetime.now()
        research_results = await asyncio.gather(
            *[self.researcher.run(subtask) for subtask in subtasks]
        )
        research_end = datetime.now()
        research_total_ms = (research_end - research_start).total_seconds() * 1000

        research_outputs = []

        for i, (subtask, result) in enumerate(zip(subtasks, research_results)):

            research_outputs.append(result.output)

            task.steps.append(
                Step(
                    agent="researcher",
                    subtask=subtask,
                    output=result.output,
                    timestamp=research_start,
                    duration_ms=round(research_total_ms, 2)
                )
            )

        # Writing
        task.status = "writing"
        save_task(task)  # live update

        t0 = datetime.now()
        writer_result = await self.writer.run(query, subtasks, research_outputs)
        t1 = datetime.now()

        draft = writer_result.output

        task.steps.append(
            Step(
                agent="writer",
                output="Draft created",
                timestamp=t0,
                duration_ms=(t1 - t0).total_seconds() * 1000
            )
        )

        # Review
        task.status = "reviewing"
        save_task(task)  # live update

        approved = False

        while not approved:

            t0 = datetime.now()
            review_result = await self.reviewer.run(draft)
            t1 = datetime.now()

            task.steps.append(
                Step(
                    agent="reviewer",
                    output=review_result.status,
                    timestamp=t0,
                    duration_ms=(t1 - t0).total_seconds() * 1000
                )
            )

            if review_result.status == "approved":
                approved = True
                break

            if review_result.status == "revision_needed":

                task.steps.append(
                    Step(
                        agent="reviewer",
                        output="Feedback: " + review_result.output,
                        timestamp=datetime.now(),
                        duration_ms=0
                    )
                )

                task.status = "writing"
                save_task(task)  # live update

                t0 = datetime.now()
                writer_result = await self.writer.run(query, subtasks, research_outputs)
                t1 = datetime.now()

                draft = writer_result.output

                task.steps.append(
                    Step(
                        agent="writer",
                        output="Revised draft created",
                        timestamp=t0,
                        duration_ms=(t1 - t0).total_seconds() * 1000
                    )
                )

                task.status = "reviewing"
                save_task(task)  # live update

        pipeline_end = datetime.now()
        task.status = "completed"
        task.result = draft
        task.end_time = pipeline_end
        task.total_duration_ms = (pipeline_end - pipeline_start).total_seconds() * 1000

        metrics_after = get_metrics()
        task.metrics = {
            "llm_calls": metrics_after["llm_calls"] - metrics_before["llm_calls"],
            "retries": metrics_after["retries"] - metrics_before["retries"],
            "duration_ms": round(task.total_duration_ms, 2),
        }

        save_task(task)

        return task