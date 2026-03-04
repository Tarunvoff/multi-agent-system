from .base_agent import Agent
from models.agent_result import AgentResult


class PlannerAgent(Agent):

    name = "planner"

    async def run(self, input_data):

        query = input_data

        subtasks = [
            "definition of microservices",
            "definition of monoliths",
            "advantages comparison",
            "disadvantages comparison",
            "final comparison summary"
        ]

        return AgentResult(
            status="success",
            output=subtasks
        )