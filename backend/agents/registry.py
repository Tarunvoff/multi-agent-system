from typing import Dict, List, Type

from agents.base_agent import Agent
from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.fact_checker_agent import FactCheckerAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent

# Maps API-facing agent names to their implementation classes.
AGENT_REGISTRY: Dict[str, Type[Agent]] = {
    "planner":     PlannerAgent,
    "researcher":  ResearcherAgent,
    "factchecker": FactCheckerAgent,
    "writer":      WriterAgent,
    "reviewer":    ReviewerAgent,
}


def build_pipeline(agent_names: List[str]) -> List[Agent]:
    """Instantiate agents in the given order.

    Raises:
        ValueError: if any name is not in AGENT_REGISTRY.
    """
    unknown = [n for n in agent_names if n not in AGENT_REGISTRY]
    if unknown:
        raise ValueError(
            f"Unknown agent(s): {unknown}. "
            f"Available: {sorted(AGENT_REGISTRY.keys())}"
        )
    return [AGENT_REGISTRY[name]() for name in agent_names]
