"""Tests for PipelineConfig model and the agent registry."""

import pytest

from agents.registry import AGENT_REGISTRY, build_pipeline
from models.pipeline import DEFAULT_PIPELINE, PipelineConfig


# ---------------------------------------------------------------------------
# PipelineConfig model
# ---------------------------------------------------------------------------

def test_default_pipeline_is_standard_four():
    config = PipelineConfig()
    assert config.agents == ["planner", "researcher", "writer", "reviewer"]


def test_default_pipeline_constant_matches_model():
    assert PipelineConfig().agents == DEFAULT_PIPELINE


def test_custom_pipeline_accepted():
    config = PipelineConfig(agents=["planner", "writer"])
    assert config.agents == ["planner", "writer"]


def test_pipeline_with_factchecker():
    config = PipelineConfig(agents=["planner", "researcher", "factchecker", "writer"])
    assert "factchecker" in config.agents


def test_empty_pipeline_accepted():
    config = PipelineConfig(agents=[])
    assert config.agents == []


# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------

def test_registry_contains_all_standard_agents():
    required = {"planner", "researcher", "writer", "reviewer", "factchecker"}
    assert required.issubset(set(AGENT_REGISTRY.keys()))


def test_build_pipeline_returns_correct_agents():
    pipeline = build_pipeline(["planner", "researcher"])
    assert len(pipeline) == 2
    assert pipeline[0].name == "planner"
    assert pipeline[1].name == "researcher"


def test_build_pipeline_with_factchecker():
    pipeline = build_pipeline(["planner", "researcher", "factchecker", "writer"])
    names = [a.name for a in pipeline]
    assert names == ["planner", "researcher", "factchecker", "writer"]


def test_build_pipeline_raises_on_unknown_agent():
    with pytest.raises(ValueError, match="Unknown agent"):
        build_pipeline(["planner", "nonexistent"])


def test_build_pipeline_each_agent_is_unique_instance():
    """build_pipeline creates fresh instances on every call."""
    p1 = build_pipeline(["planner"])
    p2 = build_pipeline(["planner"])
    assert p1[0] is not p2[0]


def test_agent_names_match_registry_keys():
    """Each agent's .name property matches its registry key."""
    for key, cls in AGENT_REGISTRY.items():
        agent = cls()
        assert agent.name == key
