from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime


class Step(BaseModel):
    agent: str
    subtask: Optional[str] = None
    output: Any
    timestamp: datetime
    duration_ms: Optional[float] = None


class Task(BaseModel):
    id: str
    query: str
    status: str
    steps: List[Step] = []
    result: Optional[Any] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    metrics: Optional[Dict] = None