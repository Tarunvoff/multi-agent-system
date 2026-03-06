"""Tests for the Orchestrator — pipeline execution, status transitions,
task persistence, and the writer-reviewer revision loop."""

import pytest

from models.pipeline import PipelineConfig
from orchestrator.orchestrator import Orchestrator
from storage.task_store import get_task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_orchestrator() -> Orchestrator:
    return Orchestrator()


# ---------------------------------------------------------------------------
# Default pipeline
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_default_pipeline_completes(mock_generate):
    """Full default pipeline (planner→researcher→writer→reviewer) completes."""
    orch = make_orchestrator()
    task = orch.create_task("Explain quantum entanglement")
    result = await orch.run(task.id)

    assert result.status == "completed"
    assert result.result is not None
    assert len(result.steps) >= 4  # planner + 3 researchers + writer + reviewer


@pytest.mark.asyncio
async def test_default_pipeline_persists_task(mock_generate):
    """Completed task is retrievable from the store."""
    orch = make_orchestrator()
    task = orch.create_task("Test persistence")
    await orch.run(task.id)

    stored = get_task(task.id)
    assert stored is not None
    assert stored.status == "completed"
    assert stored.result is not None


@pytest.mark.asyncio
async def test_pipeline_records_steps_in_order(mock_generate):
    """Steps are recorded with the correct agent names in pipeline order."""
    orch = make_orchestrator()
    task = orch.create_task("Order test")
    result = await orch.run(task.id)

    agent_names = [s.agent for s in result.steps]
    # Planner must come first
    assert agent_names[0] == "planner"
    # Researcher steps come before writer
    writer_idx = next(i for i, n in enumerate(agent_names) if n == "writer")
    researcher_indices = [i for i, n in enumerate(agent_names) if n == "researcher"]
    assert all(i < writer_idx for i in researcher_indices)


@pytest.mark.asyncio
async def test_default_pipeline_metrics_recorded(mock_generate):
    """Metrics dict is populated after a completed run."""
    orch = make_orchestrator()
    task = orch.create_task("Metrics test")
    result = await orch.run(task.id)

    assert result.metrics is not None
    assert "llm_calls" in result.metrics
    assert "duration_ms" in result.metrics
    assert result.metrics["llm_calls"] > 0


# ---------------------------------------------------------------------------
# Custom pipelines
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_planner_writer_pipeline(mock_generate):
    """Minimal pipeline without researcher completes."""
    config = PipelineConfig(agents=["planner", "writer"])
    orch = make_orchestrator()
    task = orch.create_task("Short pipeline", config)
    result = await orch.run(task.id, config)

    assert result.status == "completed"
    agent_names = [s.agent for s in result.steps]
    assert "planner" in agent_names
    assert "writer" in agent_names
    assert "researcher" not in agent_names


@pytest.mark.asyncio
async def test_pipeline_with_factchecker(mock_generate):
    """FactChecker stage is executed when included in the pipeline."""
    config = PipelineConfig(agents=["planner", "researcher", "factchecker", "writer"])
    orch = make_orchestrator()
    task = orch.create_task("Fact-check pipeline", config)
    result = await orch.run(task.id, config)

    assert result.status == "completed"
    agent_names = [s.agent for s in result.steps]
    assert "factchecker" in agent_names
    # factchecker must appear after all researcher steps
    fc_idx = agent_names.index("factchecker")
    researcher_indices = [i for i, n in enumerate(agent_names) if n == "researcher"]
    assert all(i < fc_idx for i in researcher_indices)


@pytest.mark.asyncio
async def test_pipeline_skips_reviewer_without_writer(mock_generate):
    """Reviewer can run independently; without a writer it accepts the empty draft."""
    config = PipelineConfig(agents=["planner", "researcher", "reviewer"])
    orch = make_orchestrator()
    task = orch.create_task("No-writer pipeline", config)
    result = await orch.run(task.id, config)

    assert result.status == "completed"
    agent_names = [s.agent for s in result.steps]
    assert "reviewer" in agent_names


@pytest.mark.asyncio
async def test_pipeline_stored_on_task(mock_generate):
    """The agent names used are stored on the task."""
    config = PipelineConfig(agents=["planner", "writer"])
    orch = make_orchestrator()
    task = orch.create_task("Pipeline stored", config)
    result = await orch.run(task.id, config)

    assert result.pipeline == ["planner", "writer"]


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initial_status_is_planning(mock_generate):
    orch = make_orchestrator()
    task = orch.create_task("Status check")
    assert task.status == "planning"


@pytest.mark.asyncio
async def test_status_transitions_to_completed(mock_generate):
    orch = make_orchestrator()
    task = orch.create_task("Transition test")
    result = await orch.run(task.id)
    assert result.status == "completed"
