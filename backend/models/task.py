from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class Step(BaseModel):
    agent: str
    output: Any
    timestamp: datetime


class Task(BaseModel):
    id: str
    query: str
    status: str
    steps: List[Step] = []
    result: Optional[Any] = None