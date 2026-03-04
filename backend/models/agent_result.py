from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentResult(BaseModel):
    status: str
    output: Optional[Any] = None
    metadata: Optional[Dict] = None