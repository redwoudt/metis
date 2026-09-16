"""Run the Chapter 3 State and Memento example without calling a provider."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager


@dataclass
class RecordingModelManager:
    """Return stable text and record the prompt sent by the active state."""

    role: str = "analysis"
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append((prompt, dict(kwargs)))
        return "Mêtis has started a new conversation."


def build_engine() -> ConversationEngine:
    """Create a conversation engine with the deterministic mock model."""
    return ConversationEngine(model_manager=RecordingModelManager())


def run_demo(prompt: str = "Plan a careful route home") -> dict[str, Any]:
    """Advance one state, then restore the earlier conversation checkpoint."""
    with TemporaryDirectory(prefix="metis-chapter3-") as directory:
        engine = build_engine()
        memory = MemoryManager(
            file_path=str(Path(directory) / "snapshots.pkl"),
            max_snapshots=3,
        )
        scope = "reader-03"
        engine.history.append(f"User: {prompt}")

        state_before = type(engine.state).__name__
        memory.save(engine.create_snapshot(), scope=scope)

        response = engine.respond(prompt)
        state_after_turn = type(engine.state).__name__
        history_after_turn = list(engine.history)

        restored = memory.restore_into(engine, scope=scope)
        return {
            "state_before": state_before,
            "state_after_turn": state_after_turn,
            "state_after_restore": type(engine.state).__name__,
            "history_after_turn": history_after_turn,
            "history_after_restore": list(engine.history),
            "restored": restored,
            "remaining_checkpoints": memory.count(scope=scope),
            "response": response,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="Plan a careful route home")
    return parser


def main() -> int:
    result = run_demo(build_parser().parse_args().prompt)
    for key in (
        "state_before",
        "state_after_turn",
        "state_after_restore",
        "restored",
        "remaining_checkpoints",
    ):
        print(f"{key}={result[key]}")
    print(f"history_after_restore={result['history_after_restore']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
