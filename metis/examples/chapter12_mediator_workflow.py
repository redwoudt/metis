"""Trace one mediated Mêtis request without contacting a model provider."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from metis.components.session_manager import SessionManager
from metis.handler.request_handler import RequestHandler
from metis.services.services import Services


def run_demo() -> dict[str, str | bool]:
    """Run one request through the public boundary and summarize the result."""
    previous_scheduler = os.environ.get("METIS_TASK_SCHEDULER")
    os.environ["METIS_TASK_SCHEDULER"] = "inmemory"

    try:
        with TemporaryDirectory(prefix="metis-ch12-") as data_dir:
            session_path = Path(data_dir) / "sessions.pkl"
            session_manager = SessionManager(file_path=str(session_path))
            services = Services(
                plugin_config={"enabled_plugins": (), "strict_plugins": True}
            )
            handler = RequestHandler(
                services=services,
                session_manager=session_manager,
                config={
                    "vendor": "mock",
                    "model": "chapter12",
                    "policies": {},
                },
            )

            user_id = "reader-12"
            response = handler.handle_prompt(
                user_id=user_id,
                user_input="[tone: concise] Explain why request order matters.",
            )

            session = session_manager.load_or_create(user_id)
            persisted_sessions = SessionManager(file_path=str(session_path)).memory

            return {
                "entry_point": type(handler).__name__,
                "coordinator": type(handler.mediator).__name__,
                "response_returned": bool(response),
                "session_tone": session.tone,
                "one_completion_event": (
                    services.analytics_observer.get_event_count("response.generated")
                    == 1
                ),
                "session_persisted": user_id in persisted_sessions,
            }
    finally:
        if previous_scheduler is None:
            os.environ.pop("METIS_TASK_SCHEDULER", None)
        else:
            os.environ["METIS_TASK_SCHEDULER"] = previous_scheduler


def main() -> int:
    """Print the observable result of one mediated request."""
    for key, value in run_demo().items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
