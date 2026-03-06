import json
import logging

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

log = logging.getLogger(__name__)

_FALLBACK_SUBTASKS = [
    "definition of microservices",
    "definition of monoliths",
    "advantages vs disadvantages",
]


class PlannerAgent(Agent):

    @property
    def name(self) -> str:
        return "planner"

    async def run(self, input_data: str) -> AgentResult:
        if not USE_LLM:
            return AgentResult(status="success", output=_FALLBACK_SUBTASKS)

        try:
            prompt = (
                f'Task: {input_data}\n\n'
                'Return ONLY a JSON array of exactly 3 short research subtopic strings.\n'
                'No explanation. No markdown. Example: ["subtopic 1", "subtopic 2", "subtopic 3"]'
            )
            response = (await generate(prompt, max_tokens=100)).strip()

            start, end = response.find("["), response.rfind("]") + 1
            raw = response[start:end] if start != -1 and end > start else response
            subtasks = json.loads(raw)

            return AgentResult(status="success", output=subtasks[:3])

        except Exception as e:
            log.warning("LLM error: %s", e)
            return AgentResult(status="success", output=_FALLBACK_SUBTASKS)