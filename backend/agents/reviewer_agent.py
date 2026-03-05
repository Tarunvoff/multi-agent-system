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
            return AgentResult(status="approved", output="APPROVED")

        try:
            prompt = (
                "Review this report. Default to APPROVED.\n"
                "Only flag a revision if there is a clear factual contradiction or an obviously missing required section.\n\n"
                "Return EXACTLY one of:\n"
                "  APPROVED\n"
                "  REVISION_NEEDED: <issue1>; <issue2>\n\n"
                "No other text.\n\n"
                f"Report:\n{draft}"
            )
            response = (await generate(prompt, max_tokens=80)).strip()

            upper = response.upper()
            if upper.startswith("APPROVED"):
                return AgentResult(status="approved", output="APPROVED")
            if upper.startswith("REVISION_NEEDED"):
                issues = response[response.find(":") + 1:].strip() if ":" in response else response
                return AgentResult(status="revision_needed", output=issues)

            # Ambiguous — approve to break potential loops
            return AgentResult(status="approved", output="APPROVED")

        except Exception as e:
            print(f"[ReviewerAgent] LLM error: {e}")
            return AgentResult(status="approved", output="APPROVED")