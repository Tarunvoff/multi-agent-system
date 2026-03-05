import json
from agents.base_agent import Agent
from models.agent_result import AgentResult

_FALLBACK_SUBTASKS = [
    "definition of microservices",
    "definition of monoliths",
    "advantages comparison",
    "disadvantages comparison",
    "final comparison summary",
]


class PlannerAgent(Agent):

    name = "planner"

    async def run(self, input_data):
        from config import USE_LLM

        if not USE_LLM:
            return AgentResult(status="success", output=_FALLBACK_SUBTASKS)

        try:
            from llm.llm_client import generate

            prompt = (
                "Break the following task into exactly 3 research subtasks. "
                "Return ONLY a JSON array of 3 short strings, no explanation.\n"
                f"Task: {input_data}"
            )
            response = await generate(prompt, max_tokens=150)
            response = response.strip()

            # Extract the JSON array even if the model wraps it in markdown fences
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > start:
                subtasks = json.loads(response[start:end])
            else:
                subtasks = json.loads(response)

            # Hard cap — never spawn more than 3 parallel researchers
            subtasks = subtasks[:3]

            return AgentResult(status="success", output=subtasks)

        except Exception as e:
            print(f"[PlannerAgent] LLM error: {e}")
            return AgentResult(status="success", output=_FALLBACK_SUBTASKS)