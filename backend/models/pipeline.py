from pydantic import BaseModel
from typing import List

DEFAULT_PIPELINE: List[str] = ["planner", "researcher", "writer", "reviewer"]


class PipelineConfig(BaseModel):
    """Specifies the ordered list of agent names for a pipeline run.

    Example:
        PipelineConfig(agents=["planner", "researcher", "factchecker", "writer"])
    """
    agents: List[str] = DEFAULT_PIPELINE
