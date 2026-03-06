import json
import logging

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
from llm.llm_client import generate

log = logging.getLogger(__name__)


class FactCheckerAgent(Agent):
    """Verifies and corrects research outputs before writing.

    Each item in research_outputs is a dict with 'topic' and 'facts' keys.
    Invalid or uncorrectable items are passed through unchanged.
    """

    @property
    def name(self) -> str:
        return "factchecker"

    async def run(self, research_outputs: list) -> AgentResult:
        if not USE_LLM:
            return AgentResult(status="success", output=research_outputs)

        verified = []
        for item in research_outputs:
            if not isinstance(item, dict):
                verified.append(item)
                continue

            topic = item.get("topic", "")
            facts = item.get("facts", [])

            try:
                prompt = (
                    f'Fact-check these claims about "{topic}".\n'
                    f'Claims: {json.dumps(facts)}\n\n'
                    'Return ONLY a JSON object (no markdown, no extra text):\n'
                    '{"topic": "<topic>", "facts": ["verified or corrected fact1", ...]}\n'
                    'Keep accurate facts as-is. Correct any that are wrong.'
                )
                response = (await generate(prompt, max_tokens=300)).strip()
                start, end = response.find("{"), response.rfind("}") + 1
                if start != -1 and end > start:
                    checked = json.loads(response[start:end])
                    verified.append({
                        "topic": checked.get("topic", topic),
                        "facts": checked.get("facts", facts),
                    })
                else:
                    verified.append(item)

            except Exception as e:
                log.warning("Error on topic '%s': %s", topic, e)
                verified.append(item)

        return AgentResult(status="success", output=verified)
