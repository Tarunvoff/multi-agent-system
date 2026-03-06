"""Task persistence backed by SQLite via storage.database.

All callers work with the Task Pydantic model; this module handles
serialization to/from the TaskRow table.  Swapping the storage backend
only requires changing storage.database — this interface stays the same.
"""

import json
from typing import List, Optional

from sqlmodel import Session, select

import storage.database as _db
from models.task import Step, Task
from storage.database import TaskRow


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _task_to_row(task: Task) -> TaskRow:
    steps_data = [s.model_dump(mode="json") for s in task.steps]
    return TaskRow(
        id=task.id,
        query=task.query,
        status=task.status,
        pipeline_json=json.dumps(task.pipeline or []),
        steps_json=json.dumps(steps_data),
        result_json=json.dumps(task.result) if task.result is not None else None,
        metrics_json=json.dumps(task.metrics) if task.metrics else None,
        start_time=task.start_time,
        end_time=task.end_time,
        total_duration_ms=task.total_duration_ms,
    )


def _row_to_task(row: TaskRow) -> Task:
    steps = [Step(**s) for s in json.loads(row.steps_json or "[]")]
    result = json.loads(row.result_json) if row.result_json is not None else None
    metrics = json.loads(row.metrics_json) if row.metrics_json else None
    pipeline = json.loads(row.pipeline_json) if row.pipeline_json else None

    return Task(
        id=row.id,
        query=row.query,
        status=row.status,
        pipeline=pipeline or None,
        steps=steps,
        result=result,
        metrics=metrics,
        start_time=row.start_time,
        end_time=row.end_time,
        total_duration_ms=row.total_duration_ms,
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def save_task(task: Task) -> None:
    """Insert or update a task record."""
    row = _task_to_row(task)
    with Session(_db.engine) as session:
        existing = session.get(TaskRow, task.id)
        if existing:
            for key, val in row.model_dump().items():
                setattr(existing, key, val)
        else:
            session.add(row)
        session.commit()


def get_task(task_id: str) -> Optional[Task]:
    """Return the Task for *task_id*, or None if not found."""
    with Session(_db.engine) as session:
        row = session.get(TaskRow, task_id)
        return _row_to_task(row) if row else None


def get_all_tasks() -> List[Task]:
    """Return all tasks, newest first."""
    with Session(_db.engine) as session:
        rows = session.exec(
            select(TaskRow).order_by(TaskRow.start_time.desc())
        ).all()
        return [_row_to_task(r) for r in rows]