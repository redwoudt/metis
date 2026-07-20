import pytest

from metis.components.model_manager import ModelManager
from metis.conversation_engine import ConversationEngine
from metis.memory import (
    ArtifactPool,
    ConversationMemento,
    MemoryManager,
    MissingArtifactError,
)
from metis.models.model_factory import ModelFactory
from metis.states.clarifying import ClarifyingState


def _engine(model="A") -> ConversationEngine:
    client = ModelFactory.for_role(
        "analysis", {"vendor": "mock", "model": model, "policies": {}}
    )
    return ConversationEngine(model_manager=ModelManager(client))


def _configure(engine: ConversationEngine) -> None:
    engine.configure_shared_memory(
        {
            "system_prompt": "You are Mêtis, a careful orchestration assistant.",
            "tool_schema": {"tools": [{"name": "search", "args": ["query"]}]},
            "safety_policy": {"version": 3, "rules": ["protect tenant data"]},
        }
    )


def test_lean_mementos_share_artifacts_and_restore_session_state(tmp_path):
    pool = ArtifactPool()
    memory = MemoryManager(file_path=str(tmp_path / "memory.pkl"), artifact_pool=pool)
    engine = _engine("A")
    _configure(engine)
    engine.state = ClarifyingState()
    engine.preferences["tone"] = "concise"
    engine.history = ["first response", "second response"]

    first = engine.create_memento(pool, tenant_id="tenant-a")
    second = engine.create_memento(pool, tenant_id="tenant-a")
    assert isinstance(first, ConversationMemento)
    assert first.artifact_refs == second.artifact_refs
    assert first.history_refs == second.history_refs
    assert len(pool) == 5

    memory.save(first)
    original_manager = engine.model_manager
    engine.state = None
    engine.preferences["tone"] = "playful"
    engine.history.append("not retained")
    engine.shared_artifacts = {}

    assert memory.restore_into(engine) is True
    assert isinstance(engine.state, ClarifyingState)
    assert engine.preferences["tone"] == "concise"
    assert engine.history == ["first response", "second response"]
    assert engine.shared_artifacts["tool_schema"]["tools"][0]["name"] == "search"
    assert engine.model_manager is original_manager


def test_reference_aware_trimming_releases_only_dead_artifacts(tmp_path):
    pool = ArtifactPool(max_entries=4)
    memory = MemoryManager(
        file_path=str(tmp_path / "memory.pkl"),
        artifact_pool=pool,
        max_snapshots=1,
    )
    engine = _engine()
    _configure(engine)

    engine.history = ["old response"]
    old = engine.create_memento(pool, tenant_id="tenant-a")
    old_history_reference = old.history_refs[0]
    memory.save(old)

    engine.history = ["new response"]
    new = engine.create_memento(pool, tenant_id="tenant-a")
    memory.save(new)

    assert len(memory) == 1
    assert pool.pin_count(old_history_reference) == 0
    with pytest.raises(MissingArtifactError):
        pool.resolve(old_history_reference)
    for reference in new.references:
        assert pool.pin_count(reference) == 1
        pool.resolve(reference)


def test_missing_artifact_failure_keeps_checkpoint_for_recovery(tmp_path):
    pool = ArtifactPool()
    memory = MemoryManager(file_path=str(tmp_path / "memory.pkl"), artifact_pool=pool)
    engine = _engine()
    _configure(engine)
    engine.history = ["recover me"]
    memento = engine.create_memento(pool, tenant_id="tenant-a")
    memory.save(memento)

    pool.evict(memento.history_refs[0], force=True)

    with pytest.raises(MissingArtifactError):
        memory.restore_into(engine)
    assert len(memory) == 1


def test_pool_and_memento_survive_manager_restart(tmp_path):
    file_path = str(tmp_path / "memory.pkl")
    memory = MemoryManager(file_path=file_path)
    engine = _engine()
    _configure(engine)
    engine.history = ["persisted response"]
    memory.save(engine.create_memento(memory.artifact_pool, tenant_id="tenant-a"))

    restarted = MemoryManager(file_path=file_path)
    restored_engine = _engine("B")

    assert restarted.restore_into(restored_engine) is True
    assert restored_engine.history == ["persisted response"]
    assert restored_engine.shared_artifacts["system_prompt"].startswith("You are Mêtis")
    assert "[mock:b]" in restored_engine.generate_with_model("still live").lower()
