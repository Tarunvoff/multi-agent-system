from .base_agent import Agent
from models.agent_result import AgentResult


class ResearcherAgent(Agent):

    name = "researcher"

    async def run(self, subtask):

        result = f"Research findings about {subtask}."

        return AgentResult(
            status="success",
            output=result
        )