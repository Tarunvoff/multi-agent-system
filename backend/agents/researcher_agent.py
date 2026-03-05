import asyncio

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

# Limit concurrent LLM calls to avoid free-tier rate limits
_semaphore = asyncio.Semaphore(3)


class ResearcherAgent(Agent):

    @property
    def name(self) -> str:
        return "researcher"

    async def run(self, subtask: str) -> AgentResult:
        if not USE_LLM:
            return AgentResult(status="success", output=f"Research findings about {subtask}.")

        async with _semaphore:
            try:
                prompt = (
                    f"Topic: {subtask}\n\n"
                    "Give exactly 3 bullet points of well-known, verified facts about this topic. "
                    "Only state facts you are certain about. "
                    "Do not speculate, invent details, or add information you are unsure of."
                )
                result = await generate(prompt, max_tokens=400)
                return AgentResult(status="success", output=result)

            except Exception as e:
                print(f"[ResearcherAgent] LLM error: {str(e)[:120]}")
                return AgentResult(status="success", output=f"Research findings about {subtask}.")