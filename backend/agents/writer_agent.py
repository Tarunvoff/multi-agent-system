import logging

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

log = logging.getLogger(__name__)


def _format_research(research_outputs: list) -> str:
    """Convert structured research dicts (or plain strings) into prompt-ready text."""
    sections = []
    for item in research_outputs:
        if isinstance(item, dict):
            topic = item.get("topic", "")
            facts = item.get("facts", [])
            bullet_facts = "\n".join(f"- {f}" for f in facts)
            sections.append(f"### {topic}\n{bullet_facts}")
        else:
            sections.append(str(item))
    return "\n\n".join(sections)


class WriterAgent(Agent):

    @property
    def name(self) -> str:
        return "writer"

    async def run(self, user_query: str, topics: list[str], research_outputs: list) -> AgentResult:
        research_text = _format_research(research_outputs)

        if not USE_LLM:
            return AgentResult(status="success", output=f"# Report\n\n{research_text}")

        try:
            prompt = (
                f"Request: {user_query}\n\n"
                f"Research:\n{research_text}\n\n"
                "Write a Markdown report using ONLY the facts above.\n"
                "Format: one-sentence intro, ## heading per topic, bullet facts, one-sentence conclusion.\n"
                "Max 150 words. No extra commentary."
            )
            report = await generate(prompt, max_tokens=500)
            return AgentResult(status="success", output=report)

        except Exception as e:
            log.warning("LLM error: %s", e)
            return AgentResult(status="success", output=f"# Report\n\n{research_text}")