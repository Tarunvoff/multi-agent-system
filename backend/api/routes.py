from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


class QueryRequest(BaseModel):
    query: str


@router.post("/run")
async def run_task(request: QueryRequest):
    task = await orchestrator.run(request.query)
    return task


@router.get("/health")
def health():
    return {"status": "ok"}


class _Orchestrator:

    def __init__(self):

        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    def run(self, query):

        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            query=query,
            status="planning"
        )

        # Planner
        planner_result = self.planner.run(query)

        task.steps.append(
            Step(
                agent="planner",
                output=str(planner_result.output),
                timestamp=datetime.now()
            )
        )

        subtasks = planner_result.output

        # Research
        research_outputs = []

        task.status = "researching"

        for subtask in subtasks:

            result = self.researcher.run(subtask)

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

        writer_result = self.writer.run(research_outputs)

        draft = writer_result.output

        task.steps.append(
            Step(
                agent="writer",
                output="Draft created",
                timestamp=datetime.now()
            )
        )

        # Review
        task.status = "reviewing"

        review_result = self.reviewer.run(draft)

        if review_result.status == "revision_needed":

            writer_result = self.writer.run(research_outputs)

            draft = writer_result.output

        task.steps.append(
            Step(
                agent="reviewer",
                output=review_result.status,
                timestamp=datetime.now()
            )
        )

        task.status = "completed"
        task.result = draft

        save_task(task)

        return task