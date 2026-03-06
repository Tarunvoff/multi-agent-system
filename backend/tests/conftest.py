"""Shared pytest fixtures for all backend tests.

Key fixtures
------------
in_memory_db   (autouse) — replaces the SQLite engine with :memory: so tests
               are hermetic and leave no files on disk.
mock_generate  — patches llm.llm_client.generate with a fast, deterministic
               stub that returns valid JSON for each agent type.
"""

import sys
import os

# Ensure the backend package root is importable regardless of where pytest
# is invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import SQLModel, create_engine

import storage.database as _db
import llm.llm_client as _llm_client


# ---------------------------------------------------------------------------
# Database fixture — in-memory SQLite per test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def in_memory_db():
    """Replace the shared engine with a fresh in-memory database for every test."""
    test_engine = create_engine("sqlite:///:memory:")
    original_engine = _db.engine
    _db.engine = test_engine
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    _db.engine = original_engine


# ---------------------------------------------------------------------------
# LLM mock fixture
# ---------------------------------------------------------------------------

async def _fake_generate(prompt: str, max_tokens: int = 600) -> str:
    """Return minimal but structurally valid responses for every agent prompt."""
    _llm_client._metrics["llm_calls"] += 1
    if "JSON array" in prompt:
        return '["subtopic alpha", "subtopic beta", "subtopic gamma"]'
    if "JSON object for this topic" in prompt:
        return '{"topic": "test topic", "facts": ["fact 1.", "fact 2.", "fact 3."]}'
    if "Write a Markdown report" in prompt:
        return "# Test Report\n\nThis is a test report.\n\n## Conclusion\n\nDone."
    if "Review this report" in prompt:
        return "APPROVED"
    if "Fact-check these claims" in prompt:
        return '{"topic": "test topic", "facts": ["verified 1.", "verified 2.", "verified 3."]}'
    return "Generic test response."


@pytest.fixture
def mock_generate():
    """Patch generate in every agent module (where it is directly imported)."""
    from contextlib import ExitStack

    targets = [
        "agents.planner_agent.generate",
        "agents.researcher_agent.generate",
        "agents.writer_agent.generate",
        "agents.reviewer_agent.generate",
        "agents.fact_checker_agent.generate",
    ]
    with ExitStack() as stack:
        first = None
        for target in targets:
            m = stack.enter_context(patch(target, new_callable=AsyncMock))
            m.side_effect = _fake_generate
            if first is None:
                first = m
        yield first
