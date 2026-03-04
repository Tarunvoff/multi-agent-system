from .base_agent import Agent
from models.agent_result import AgentResult


class WriterAgent(Agent):

    name = "writer"

    async def run(self, research_outputs):

        draft = "\n".join(research_outputs)

        report = f"Final Report:\n\n{draft}"

        return AgentResult(
            status="success",
            output=report
        )