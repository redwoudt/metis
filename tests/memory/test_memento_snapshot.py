from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager

# --- helpers -----------------------------------------------------------------

def _engine(vendor="mock", model="A") -> ConversationEngine:
    client = ModelFactory.for_role("analysis", {"vendor": vendor, "model": model, "policies": {}})
    manager = ModelManager(client)
    return ConversationEngine(model_manager=manager)


class _EchoState:
    """Simple state exercising the bridge hook."""
    def respond(self, engine, user_input: str) -> str:
        return engine.generate_with_model(f"echo::{user_input}")

class _OtherState:
    def respond(self, engine, user_input: str) -> str:
        return engine.generate_with_model(f"other::{user_input}")

# --- tests -------------------------------------------------------------------

def test_snapshot_restore_keeps_model_manager():
    engine = _engine(vendor="mock", model="A")
    engine.set_state(_EchoState())
    out_a = engine.respond("hello")
    assert "[mock:a]" in out_a.lower()

    snap = engine.create_snapshot()

    # Swap adapter after snapshot
    engine.set_model_manager(ModelManager(
        ModelFactory.for_role("analysis", {"vendor": "mock", "model": "B", "policies": {}})
    ))
    out_b = engine.respond("hello")
    assert "[mock:b]" in out_b.lower()

    # Restore snapshot -> back to previous adapter ("A")
    engine.restore_snapshot(snap)
    out_restored = engine.respond("hello")
    assert "[mock:a]" in out_restored.lower()


def test_snapshot_roundtrip_restores_state_and_history():
    engine = _engine()
    engine.set_state(_EchoState())
    engine.preferences["tone"] = "serious"

    # interact
    r1 = engine.respond("one")
    assert "echo::one" in r1.lower()
    assert len(engine.history) == 1

    snap = engine.create_snapshot()

    # mutate: state, prefs, history
    engine.set_state(_OtherState())
    engine.preferences["tone"] = "playful"
    r2 = engine.respond("two")
    assert "other::two" in r2.lower()
    assert len(engine.history) == 2

    # restore to snapshot
    engine.restore_snapshot(snap)

    # state restored -> back to _EchoState
    r3 = engine.respond("three")
    assert "echo::three" in r3.lower()
    assert engine.preferences["tone"] == "serious"
    # history restored to the pre-mutation list
    assert len(engine.history) == 2  # ["echo::one", "echo::three"]


def test_snapshot_restore_isolation_from_future_changes():
    engine = _engine()
    engine.set_state(_EchoState())

    # initial run + snapshot
    first = engine.respond("alpha")
    assert "echo::alpha" in first.lower()
    snap = engine.create_snapshot()

    # change adapter + state
    engine.set_model_manager(ModelManager(
        ModelFactory.for_role("analysis", {"vendor": "mock", "model": "Z", "policies": {}})
    ))
    engine.set_state(_OtherState())
    second = engine.respond("beta")
    assert "[mock:z]" in second.lower()
    assert "other::beta" in second.lower()

    # restore snapshot should roll back both state and adapter
    engine.restore_snapshot(snap)
    third = engine.respond("gamma")
    assert "echo::gamma" in third.lower()
    assert "[mock:z]" not in third.lower()  # back to original adapter from snapshot