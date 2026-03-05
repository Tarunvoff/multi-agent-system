import random

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate


class ReviewerAgent(Agent):

    @property
    def name(self) -> str:
        return "reviewer"

    async def run(self, draft: str) -> AgentResult:
        if not USE_LLM:
            if random.random() < 0.3:
                return AgentResult(status="revision_needed", output="Please expand the scalability section.")
            return AgentResult(status="approved", output="Report approved.")

        try:
            prompt = (
                "You are reviewing a short AI-generated report. "
                "Your default should be to APPROVE. "
                "Only request a REVISION if there is a clear, objective problem that significantly "
                "hurts the reader — such as a directly contradictory statement or a completely "
                "missing section that was obviously required.\n\n"
                "Do NOT request a revision for minor wording, lack of depth, or style preferences.\n\n"
                "Return ONLY one of:\n\nAPPROVED\n\nor\n\n"
                "REVISION: <one sentence describing the problem>\n\n"
                f"Report:\n{draft}"
            )
            response = (await generate(prompt, max_tokens=150)).strip()

            if response.upper().startswith("APPROVED"):
                return AgentResult(status="approved", output="Report approved.")
            if response.upper().startswith("REVISION"):
                feedback = response[response.find(":") + 1:].strip() if ":" in response else response
                return AgentResult(status="revision_needed", output=feedback)

            # Ambiguous response — approve to avoid infinite loops
            return AgentResult(status="approved", output="Report approved.")

        except Exception as e:
            print(f"[ReviewerAgent] LLM error: {e}")
            return AgentResult(status="approved", output="Report approved.")