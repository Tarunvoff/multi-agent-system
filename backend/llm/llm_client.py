import asyncio
import httpx
from google import genai as _genai

import config

# ---------------------------------------------------------------------------
# Lightweight metrics — global counters snapshotted per-task by orchestrator
# ---------------------------------------------------------------------------
_metrics: dict = {"llm_calls": 0, "retries": 0}

_MAX_RETRIES = 3
_RETRY_DELAYS = [3, 6, 12]

# Shared HTTP client — avoids TCP setup cost on every LLM call
_http = httpx.AsyncClient(timeout=None)


def get_metrics() -> dict:
    return dict(_metrics)


async def generate(prompt: str, max_tokens: int = 600) -> str:
    """Call the configured LLM provider and return generated text.

    Retries up to 3 times with exponential backoff (3 s, 6 s, 12 s).
    """
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            _metrics["llm_calls"] += 1
            if config.LLM_PROVIDER == "gemini":
                return await _generate_gemini(prompt)
            if config.LLM_PROVIDER == "ollama":
                return await _generate_ollama(prompt, max_tokens)
            return await _generate_openai(prompt, max_tokens)

        except Exception as exc:
            last_exc = exc
            is_rate_limit = "429" in str(exc) or (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response.status_code == 429
            )
            if attempt < _MAX_RETRIES - 1:
                _metrics["retries"] += 1
                delay = _RETRY_DELAYS[attempt]
                label = "Rate limited (429)" if is_rate_limit else f"Error: {str(exc)[:80]}"
                print(f"[LLMClient] {label}. Retrying in {delay}s ({attempt + 1}/{_MAX_RETRIES})")
                await asyncio.sleep(delay)
            else:
                print(f"[LLMClient] All {_MAX_RETRIES} attempts failed. Last: {str(exc)[:80]}")

    raise last_exc


async def _generate_ollama(prompt: str, max_tokens: int = 600) -> str:
    response = await _http.post(
        f"{config.OLLAMA_BASE_URL}/v1/chat/completions",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": max_tokens,
        },
        timeout=600.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def _generate_openai(prompt: str, max_tokens: int = 600) -> str:
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    response = await _http.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        json={
            "model": config.OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": max_tokens,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def _generate_gemini(prompt: str) -> str:
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
    client = _genai.Client(api_key=config.GEMINI_API_KEY)
    response = await client.aio.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
    )
    return response.text
