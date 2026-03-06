"""SQLite-backed storage using SQLModel.

The TaskRow table mirrors the Task Pydantic model.  Steps are stored as a
JSON column so we avoid a separate join table while keeping the schema simple.

To swap the backend (e.g. PostgreSQL) set the DATABASE_URL environment
variable — all other code goes through task_store.py and stays unchanged.
"""

import json
import os
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine

_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
engine = create_engine(_DATABASE_URL, echo=False)


class TaskRow(SQLModel, table=True):
    __tablename__ = "tasks"

    id: str = Field(primary_key=True)
    query: str
    status: str
    pipeline_json: str = Field(default='["planner","researcher","writer","reviewer"]')
    steps_json: str = Field(default="[]")
    result_json: Optional[str] = Field(default=None)
    metrics_json: Optional[str] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    total_duration_ms: Optional[float] = Field(default=None)


def init_db() -> None:
    """Create all tables if they do not already exist."""
    SQLModel.metadata.create_all(engine)
