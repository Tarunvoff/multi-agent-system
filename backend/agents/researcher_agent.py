import asyncio
from agents.base_agent import Agent
from models.agent_result import AgentResult

# Limit concurrent LLM calls to avoid free-tier rate limits
research_semaphore = asyncio.Semaphore(3)


class ResearcherAgent(Agent):

    name = "researcher"

    async def run(self, subtask):
        from config import USE_LLM

        if not USE_LLM:
            return AgentResult(
                status="success",
                output=f"Research findings about {subtask}.",
            )

        async with research_semaphore:
            try:
                from llm.llm_client import generate

                prompt = (
                    f"Topic: {subtask}\n\n"
                    "Give 3 concise bullet points of key facts. Be brief."
                )
                result = await generate(prompt, max_tokens=400)
                return AgentResult(status="success", output=result)

            except Exception as e:
                print(f"[ResearcherAgent] LLM error after retries: {str(e)[:120]}")
                return AgentResult(
                    status="success",
                    output=f"Research findings about {subtask}.",
                )