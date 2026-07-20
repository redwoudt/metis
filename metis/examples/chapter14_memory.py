"""Runnable Chapter 14 demonstration: Flyweight plus Memento at scale."""

from __future__ import annotations

import os
import pickle
from tempfile import TemporaryDirectory

from metis.components.model_manager import ModelManager
from metis.conversation_engine import ConversationEngine
from metis.memory import ArtifactPool, MemoryManager
from metis.models.model_factory import ModelFactory


def build_engine() -> ConversationEngine:
    client = ModelFactory.for_role(
        "analysis",
        {"vendor": "mock", "model": "chapter-14", "policies": {}},
    )
    engine = ConversationEngine(model_manager=ModelManager(client))
    engine.configure_shared_memory(
        {
            "system_prompt": (
                "You are Mêtis, a precise orchestration assistant. " * 80
            ).strip(),
            "tool_schema": {
                "tools": [
                    {
                        "name": f"knowledge_search_{index}",
                        "description": "Search approved tenant knowledge safely.",
                        "arguments": {"query": "string", "limit": "integer"},
                    }
                    for index in range(30)
                ]
            },
            "safety_policy": {
                "version": "2026-07",
                "rules": [
                    f"Policy rule {index}: protect tenant data and audit tool access."
                    for index in range(60)
                ],
            },
        }
    )
    return engine


def main() -> None:
    with TemporaryDirectory(prefix="metis-chapter14-") as directory:
        file_path = os.path.join(directory, "memory.pkl")
        pool = ArtifactPool()
        memory = MemoryManager(file_path=file_path, artifact_pool=pool)
        engine = build_engine()
        baseline_snapshots = []
        lean_mementos = []

        for turn in range(1, 4):
            engine.history.append(
                f"Turn {turn}: " + "A measured response from Mêtis. " * 25
            )
            baseline_snapshots.append(engine.create_snapshot())
            memento = engine.create_memento(pool, tenant_id="acme")
            lean_mementos.append(memento)
            memory.save(memento)

        # Production checkpoint stores commonly serialize records independently.
        # Summing those records avoids pickle's process-local memo table masking
        # the duplication that exists across separately persisted snapshots.
        baseline_bytes = sum(
            len(pickle.dumps(snapshot, protocol=pickle.HIGHEST_PROTOCOL))
            for snapshot in baseline_snapshots
        )
        optimized_bytes = os.path.getsize(file_path)
        logical_references = sum(len(memento.references) for memento in lean_mementos)
        guarded_reference = lean_mementos[0].artifact_refs[0][1]

        expected_history = list(engine.history)
        engine.history.append("This mutation should disappear after restoration.")
        restored = memory.restore_into(engine)

        print("Chapter 14 — Flyweight + Memento")
        print(f"Logical artifact references : {logical_references}")
        print(f"Unique stored artifacts     : {len(pool)}")
        print("Reference reuse ratio       : " f"{logical_references / len(pool):.2f}x")
        print(f"Full-snapshot bytes         : {baseline_bytes:,}")
        print(f"Lean persistent bytes       : {optimized_bytes:,}")
        print(
            "Storage reduction           : "
            f"{(1 - optimized_bytes / baseline_bytes) * 100:.1f}%"
        )
        print(
            f"Observable state restored   : {restored and engine.history == expected_history}"
        )
        print(
            "Eviction while referenced   : "
            f"{'blocked' if not pool.evict(guarded_reference) else 'unexpected'}"
        )

        memory.trim(keep_latest=0)
        print(
            "Eviction after release      : "
            f"{'allowed' if pool.evict(guarded_reference) else 'not found'}"
        )


if __name__ == "__main__":
    main()
