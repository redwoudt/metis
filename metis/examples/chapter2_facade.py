"""Run the Chapter 2 Facade example without contacting a model provider."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from metis.components.session_manager import SessionManager
from metis.handler.request_handler import RequestHandler
from metis.services.services import Services


def run_example(*, details: bool = False) -> dict[str, Any]:
    """Send one request through the public Facade and report its boundary."""
    os.environ.setdefault("METIS_TASK_SCHEDULER", "inmemory")
    services = Services(
        plugin_config={"enabled_plugins": (), "strict_plugins": True}
    )
    with TemporaryDirectory(prefix="metis-chapter2-") as directory:
        handler = RequestHandler(
            config={"vendor": "mock", "model": "chapter2", "policies": {}},
            services=services,
            session_manager=SessionManager(
                file_path=str(Path(directory) / "sessions.pkl")
            ),
        )
        prompt = "Explain why one request entry point helps."

        if details:
            result = handler.run("reader-02", prompt)
            response_type = type(result).__name__
            response = result.response
        else:
            response = handler.handle_prompt("reader-02", prompt)
            response_type = type(response).__name__

        return {
            "entry_point": type(handler).__name__,
            "lifecycle_owner": type(handler.mediator).__name__,
            "shared_services": handler.services is handler.mediator.services,
            "response_type": response_type,
            "response": response,
        }


def main() -> None:
    """Print the observable Facade contract."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--details",
        action="store_true",
        help="return the immutable RequestResult rather than compatibility text",
    )
    args = parser.parse_args()

    outcome = run_example(details=args.details)
    for key in (
        "entry_point",
        "lifecycle_owner",
        "shared_services",
        "response_type",
    ):
        print(f"{key}={outcome[key]}")
    print(outcome["response"])


if __name__ == "__main__":  # pragma: no cover
    main()
