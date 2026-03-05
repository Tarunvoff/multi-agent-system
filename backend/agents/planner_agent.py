import json

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

_FALLBACK_SUBTASKS = [
    "definition of microservices",
    "definition of monoliths",
    "advantages comparison",
    "disadvantages comparison",
    "final comparison summary",
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
                "Break the following task into exactly 3 research subtasks. "
                "Return ONLY a JSON array of 3 short strings, no explanation.\n"
                f"Task: {input_data}"
            )
            response = (await generate(prompt, max_tokens=150)).strip()

            # Extract JSON array even if the model wraps it in markdown fences
            start, end = response.find("["), response.rfind("]") + 1
            raw = response[start:end] if start != -1 and end > start else response
            subtasks = json.loads(raw)

            return AgentResult(status="success", output=subtasks[:3])

        except Exception as e:
            print(f"[PlannerAgent] LLM error: {e}")
            return AgentResult(status="success", output=_FALLBACK_SUBTASKS)