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
    """Start the pipeline in the background and return the initial task immediately.
    The client should poll GET /task/{id} to follow live status updates.
    """
    import uuid
    from datetime import datetime
    from models.task import Task
    from storage.task_store import save_task

    # Create and persist the initial task so polling can find it straight away
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        query=request.query,
        status="planning",
        start_time=datetime.now(),
    )
    save_task(task)

    # Fire the full pipeline as a background coroutine — do NOT await it
    asyncio.create_task(orchestrator.run(request.query, task_id=task_id))

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

    timeline = []

    for i, step in enumerate(task.steps):
        timeline.append({
            "step": i + 1,
            "agent": step.agent,
            "timestamp": step.timestamp.isoformat(),
            "duration_ms": round(step.duration_ms, 2) if step.duration_ms is not None else None,
            "output_preview": (
                str(step.output)[:120] + "..."
                if len(str(step.output)) > 120
                else str(step.output)
            )
        })

    return {
        "task_id": task.id,
        "query": task.query,
        "status": task.status,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "total_duration_ms": round(task.total_duration_ms, 2) if task.total_duration_ms else None,
        "timeline": timeline
    }


@router.get("/task/{task_id}/pipeline")
def get_pipeline(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build pipeline stages
    stages = {}
    for step in task.steps:
        agent = step.agent
        if agent not in stages:
            stages[agent] = {"agent": agent, "runs": 0, "total_ms": 0.0}
        stages[agent]["runs"] += 1
        stages[agent]["total_ms"] += step.duration_ms or 0.0

    stage_list = list(stages.values())

    # ASCII pipeline diagram
    node_labels = []
    for s in stage_list:
        if s["agent"] == "researcher" and s["runs"] > 1:
            node_labels.append(f"[Researcher x{s['runs']} ⚡parallel]")
        else:
            label = s["agent"].capitalize()
            node_labels.append(f"[{label}]")

    ascii_pipeline = " → ".join(node_labels) + " → ✅ Done"

    # Bar chart (max bar = 30 chars)
    max_ms = max((s["total_ms"] for s in stage_list), default=1) or 1

    bars = []
    for s in stage_list:
        bar_len = int((s["total_ms"] / max_ms) * 30)
        bar = "█" * bar_len
        bars.append(
            f"  {s['agent']:<12} | {bar:<30} | {round(s['total_ms'], 1)} ms"
        )

    return {
        "task_id": task.id,
        "total_duration_ms": round(task.total_duration_ms, 2) if task.total_duration_ms else None,
        "pipeline_diagram": ascii_pipeline,
        "stage_breakdown": stage_list,
        "duration_chart": bars
    }