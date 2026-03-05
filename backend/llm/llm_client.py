import asyncio
import os
import httpx
from google import genai

# ---------------------------------------------------------------------------
# Lightweight metrics — global counters snapshotted per-task by orchestrator
# ---------------------------------------------------------------------------
_metrics: dict = {"llm_calls": 0, "retries": 0}

# Retry configuration: up to 3 attempts, delays 3 s → 6 s → 12 s
_MAX_RETRIES = 3
_RETRY_DELAYS = [3, 6, 12]


def get_metrics() -> dict:
    """Return a snapshot of the current global LLM metrics."""
    return dict(_metrics)


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "gemini")


async def generate(prompt: str, max_tokens: int = 600) -> str:
    """Call the configured LLM and return the generated text.

    Retries up to 3 times with exponential backoff (3 s, 6 s, 12 s).
    Handles HTTP 429 rate-limit responses gracefully.
    """
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            _metrics["llm_calls"] += 1
            provider = _provider()
            if provider == "gemini":
                return await _generate_gemini(prompt)
            if provider == "ollama":
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
                if is_rate_limit:
                    print(
                        f"[LLMClient] Rate limited (429). "
                        f"Retrying in {delay}s (attempt {attempt + 1}/{_MAX_RETRIES})"
                    )
                else:
                    print(
                        f"[LLMClient] Error: {str(exc)[:100]}. "
                        f"Retrying in {delay}s (attempt {attempt + 1}/{_MAX_RETRIES})"
                    )
                await asyncio.sleep(delay)
            else:
                print(
                    f"[LLMClient] All {_MAX_RETRIES} attempts failed. "
                    f"Last error: {str(exc)[:100]}"
                )

    raise last_exc


async def _generate_ollama(prompt: str, max_tokens: int = 600) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3:8b")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_tokens,
            },
            timeout=600.0,  # local inference can be slow
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _generate_openai(prompt: str, max_tokens: int = 600) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_tokens,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _generate_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text
