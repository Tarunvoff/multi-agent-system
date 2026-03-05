from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate


class WriterAgent(Agent):

    @property
    def name(self) -> str:
        return "writer"

    async def run(self, user_query: str, topics: list[str], research_outputs: list[str]) -> AgentResult:
        if not USE_LLM:
            return AgentResult(status="success", output="Final Report:\n\n" + "\n".join(research_outputs))

        try:
            topics_str = "\n".join(f"- {t}" for t in topics)
            notes = "\n\n".join(research_outputs)
            prompt = (
                f"User Request: {user_query}\n\n"
                f"Research Topics:\n{topics_str}\n\n"
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
            return AgentResult(status="success", output="Final Report:\n\n" + "\n".join(research_outputs))