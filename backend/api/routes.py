import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestrator.orchestrator import Orchestrator
from storage.task_store import get_task

router = APIRouter()
orchestrator = Orchestrator()


class QueryRequest(BaseModel):
    query: str


@router.post("/run")
async def run_task(request: QueryRequest):
    """Create a task, start the pipeline in the background, and return immediately.
    Poll GET /task/{id} to follow live status updates.
    """
    task = orchestrator.create_task(request.query)
    asyncio.create_task(orchestrator.run(task.id))
    return task


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/task/{task_id}")
def get_task_by_id(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/task/{task_id}/timeline")
def get_timeline(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "query": task.query,
        "status": task.status,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "total_duration_ms": round(task.total_duration_ms, 2) if task.total_duration_ms else None,
        "timeline": [
            {
                "step": i + 1,
                "agent": step.agent,
                "timestamp": step.timestamp.isoformat(),
                "duration_ms": round(step.duration_ms, 2) if step.duration_ms is not None else None,
                "output_preview": str(step.output)[:120] + ("..." if len(str(step.output)) > 120 else ""),
            }
            for i, step in enumerate(task.steps)
        ],
    }


@router.get("/task/{task_id}/pipeline")
def get_pipeline(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    stages: dict[str, dict] = {}
    for step in task.steps:
        s = stages.setdefault(step.agent, {"agent": step.agent, "runs": 0, "total_ms": 0.0})
        s["runs"] += 1
        s["total_ms"] += step.duration_ms or 0.0

    return {
        "task_id": task.id,
        "total_duration_ms": round(task.total_duration_ms, 2) if task.total_duration_ms else None,
        "stages": list(stages.values()),
    }