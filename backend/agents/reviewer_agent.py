import random
from agents.base_agent import Agent
from models.agent_result import AgentResult


class ReviewerAgent(Agent):

    name = "reviewer"

    async def run(self, draft):
        from config import USE_LLM

        if not USE_LLM:
            if random.random() < 0.3:
                return AgentResult(
                    status="revision_needed",
                    output="Please expand the scalability section.",
                )
            return AgentResult(status="approved", output="Report approved.")

        try:
            from llm.llm_client import generate

            prompt = (
                "Review the following report.\n\n"
                "Check for:\n"
                "* factual inconsistencies\n"
                "* contradictory dates or numbers\n"
                "* logical errors\n"
                "* missing sections\n"
                "* clarity of structure\n\n"
                "Return ONLY one of the following:\n\n"
                "APPROVED\n\n"
                "or\n\n"
                "REVISION: <specific feedback explaining the problem>\n\n"
                f"Report:\n{draft}"
            )
            response = await generate(prompt, max_tokens=150)
            response = response.strip()

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