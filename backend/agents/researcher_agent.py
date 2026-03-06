import asyncio
import json
import logging

from agents.base_agent import Agent
from models.agent_result import AgentResult
from config import USE_LLM
import config as _config
from llm.llm_client import generate

log = logging.getLogger(__name__)

# Per-subtask timeout: fall back to stub instead of blocking the pipeline.
_RESEARCHER_TIMEOUT = 120.0

# Lazily-created semaphore, recreated whenever a new event loop is detected.
# For local Ollama (single-threaded inference) we serialize calls (limit = 1)
# to avoid silent internal queuing that makes the pipeline appear stuck.
# Cloud providers (Gemini / OpenAI) can handle up to 3 concurrent calls.
_semaphore: asyncio.Semaphore | None = None
_semaphore_loop: asyncio.AbstractEventLoop | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore, _semaphore_loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    if _semaphore is None or _semaphore_loop is not loop:
        limit = 1 if _config.LLM_PROVIDER == "ollama" else 3
        _semaphore = asyncio.Semaphore(limit)
        _semaphore_loop = loop
    return _semaphore


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

        async with _get_semaphore():
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
                response = (
                    await asyncio.wait_for(
                        generate(prompt, max_tokens=250),
                        timeout=_RESEARCHER_TIMEOUT,
                    )
                ).strip()
                return AgentResult(status="success", output=_parse_research(response, subtask))

            except asyncio.TimeoutError:
                log.warning("Timeout (%.0fs) for subtask: %r", _RESEARCHER_TIMEOUT, subtask)
                return AgentResult(status="success", output=_fallback(subtask))
            except Exception as e:
                log.warning("LLM error: %s", str(e)[:120])
                return AgentResult(status="success", output=_fallback(subtask))