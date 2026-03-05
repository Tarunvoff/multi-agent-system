import os

# Set USE_LLM=false in environment or .env to fall back to hardcoded responses
USE_LLM: bool = os.getenv("USE_LLM", "true").lower() == "true"

# LLM provider: "openai", "gemini", or "ollama"
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Ollama (local) settings
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
