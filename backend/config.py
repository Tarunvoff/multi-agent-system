import os

# Set USE_LLM=false in environment or .env to fall back to hardcoded responses
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"

# LLM provider: "openai", "gemini", or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Ollama (local) settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
