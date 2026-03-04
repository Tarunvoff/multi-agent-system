import uuid
import asyncio
from datetime import datetime

from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent

from models.task import Task, Step
from storage.task_store import save_task


class Orchestrator:

    def __init__(self):

        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    async def run(self, query):

        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            query=query,
            status="planning"
        )

        # Planner
        planner_result = await self.planner.run(query)

        task.steps.append(
            Step(
                agent="planner",
                output=planner_result.output,
                timestamp=datetime.now()
            )
        )

        subtasks = planner_result.output

        # Research — all subtasks run in parallel
        research_outputs = []

        task.status = "researching"

        research_results = await asyncio.gather(
            *[self.researcher.run(subtask) for subtask in subtasks]
        )

        for subtask, result in zip(subtasks, research_results):

            research_outputs.append(result.output)

            task.steps.append(
                Step(
                    agent="researcher",
                    output=result.output,
                    timestamp=datetime.now()
                )
            )

        # Writing
        task.status = "writing"

        writer_result = await self.writer.run(research_outputs)

        draft = writer_result.output

        task.steps.append(
            Step(
                agent="writer",
                output="Draft created",
                timestamp=datetime.now()
            )
        )

        # Revie
        task.status = "reviewing"

        approved = False

        while not approved:

            review_result = await self.reviewer.run(draft)

            task.steps.append(
                Step(
                    agent="reviewer",
                    output=review_result.status,
                    timestamp=datetime.now()
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
                        timestamp=datetime.now()
                    )
                )

                writer_result = await self.writer.run(research_outputs)

                draft = writer_result.output

                task.steps.append(
                    Step(
                        agent="writer",
                        output="Revised draft created",
                        timestamp=datetime.now()
                    )
                )

        task.status = "completed"
        task.result = draft

        save_task(task)

        return task