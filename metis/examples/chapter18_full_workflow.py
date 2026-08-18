"""Run the Chapter 18 workflow without contacting a model provider."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from metis.components.session_manager import SessionManager
from metis.handler import RequestHandler
from metis.inspection import TraceVisitor
from metis.memory.manager import MemoryManager
from metis.services.services import Services


def main() -> None:
    """Compose, execute, inspect, and checkpoint one complete request."""
    os.environ.setdefault("METIS_TASK_SCHEDULER", "inmemory")

    with TemporaryDirectory(prefix="metis-ch18-") as data_dir:
        root = Path(data_dir)
        services = Services(
            plugin_config={"enabled_plugins": (), "strict_plugins": True}
        )
        memory = MemoryManager(file_path=str(root / "snapshots.pkl"))
        handler = RequestHandler(
            services=services,
            session_manager=SessionManager(file_path=str(root / "sessions.pkl")),
            memory_manager=memory,
            config={"vendor": "mock", "model": "chapter18", "policies": {}},
        )

        result = handler.run(
            "reader-18",
            "[behavior:balanced][tone:concise] Explain workflow checkpoints.",
            save=True,
        )
        visitor = services.inspection_service.run(
            result.execution_trace,
            TraceVisitor(),
        )

        print(result.response)
        print(f"correlation_id={result.correlation_id}")
        print(f"trace={' -> '.join(visitor.steps)}")
        print(f"checkpoint_saved={result.checkpoint_saved}")
        print(f"checkpoints={memory.count(scope='reader-18')}")


if __name__ == "__main__":  # pragma: no cover
    main()
