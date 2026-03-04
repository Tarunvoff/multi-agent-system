from .base_agent import Agent
from models.agent_result import AgentResult
import random


class ReviewerAgent(Agent):

    name = "reviewer"

    async def run(self, draft):

        if random.random() < 0.3:

            return AgentResult(
                status="revision_needed",
                output="Please expand the scalability section."
            )

        return AgentResult(
            status="approved",
            output="Report approved."
        )