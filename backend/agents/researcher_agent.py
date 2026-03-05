import asyncio
import json

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

# Limit concurrent LLM calls to avoid free-tier rate limits
_semaphore = asyncio.Semaphore(3)


def _fallback(subtask: str) -> dict:
    return {"topic": subtask, "facts": [f"Research findings about {subtask}."]}


def _parse_research(response: str, subtask: str) -> dict:
    """Extract the first JSON object from the LLM response."""
    start, end = response.find("{"), response.rfind("}") + 1
    if start == -1 or end <= start:
        return _fallback(subtask)
    data = json.loads(response[start:end])
    # Normalise: ensure topic and facts keys exist
    return {
        "topic": data.get("topic", subtask),
        "facts": data.get("facts", data.get("key_points", [])),
    }


class ResearcherAgent(Agent):

    @property
    def name(self) -> str:
        return "researcher"

    async def run(self, subtask: str) -> AgentResult:
        if not USE_LLM:
            return AgentResult(status="success", output=_fallback(subtask))

        async with _semaphore:
            try:
                prompt = (
                    f'Return a JSON object for this topic: "{subtask}"\n\n'
                    'Required format (no markdown, no extra text):\n'
                    '{"topic": "<topic>", "facts": ["fact1", "fact2", "fact3"]}\n\n'
                    'Rules:\n'
                    '- Exactly 3 facts\n'
                    '- Each fact: one concise sentence, verified and certain\n'
                    '- No speculation or invented details'
                )
                response = (await generate(prompt, max_tokens=250)).strip()
                return AgentResult(status="success", output=_parse_research(response, subtask))

            except Exception as e:
                print(f"[ResearcherAgent] LLM error: {str(e)[:120]}")
                return AgentResult(status="success", output=_fallback(subtask))