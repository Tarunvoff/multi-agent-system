from agents.base_agent import Agent
from models.agent_result import AgentResult


class WriterAgent(Agent):

    name = "writer"

    async def run(self, user_query: str, topics: list[str], research_outputs: list[str]):
        from config import USE_LLM

        if not USE_LLM:
            draft = "\n".join(research_outputs)
            return AgentResult(status="success", output=f"Final Report:\n\n{draft}")

        try:
            from llm.llm_client import generate

            topics_str = "\n".join(f"- {t}" for t in topics)
            notes = "\n\n".join(research_outputs)
            prompt = (
                f"User Request: {user_query}\n\n"
                f"Research Notes:\n{notes}\n\n"
                "Write a clear Markdown report answering the request. "
                "Use ## headings for each topic, a short intro, and a brief conclusion. "
                "IMPORTANT: Only use facts that appear in the Research Notes above. "
                "Do not add any information, statistics, or claims not present in the notes."
            )
            report = await generate(prompt, max_tokens=900)
            return AgentResult(status="success", output=report)

        except Exception as e:
            print(f"[WriterAgent] LLM error: {e}")
            draft = "\n".join(research_outputs)
            return AgentResult(status="success", output=f"Final Report:\n\n{draft}")