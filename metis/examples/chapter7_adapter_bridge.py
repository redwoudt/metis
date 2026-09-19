"""Trace one prompt through Mêtis with two deterministic provider adapters."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from metis.components.session_manager import SessionManager
from metis.handler.request_handler import RequestHandler
from metis.services.services import Services


PROMPT = "Explain why a stable model boundary matters."


def ask(handler: RequestHandler, prompt: str) -> str:
    """Call the public request boundary without provider-specific knowledge."""
    return handler.handle_prompt("chapter-7-reader", prompt)


def build_handler(vendor: str, session_file: Path) -> RequestHandler:
    """Assemble the normal request path for one deterministic built-in adapter."""
    services = Services(plugin_candidates=())
    return RequestHandler(
        config={"vendor": vendor, "model": f"chapter-7-{vendor}", "policies": {}},
        services=services,
        session_manager=SessionManager(file_path=str(session_file)),
    )


def run_demo(prompt: str = PROMPT) -> dict[str, str]:
    """Return the stable text contract for two adapters and one named failure."""
    with (
        TemporaryDirectory(prefix="metis-chapter7-") as temp_dir,
        patch.dict("os.environ", {"METIS_TASK_SCHEDULER": "inmemory"}),
    ):
        session_file = Path(temp_dir) / "sessions.pkl"
        openai_text = ask(build_handler("openai", session_file), prompt)
        anthropic_text = ask(build_handler("anthropic", session_file), prompt)

        try:
            ask(build_handler("unsupported", session_file), prompt)
        except ValueError as exc:
            unsupported_vendor_error = str(exc)
        else:  # pragma: no cover - ModelFactory must reject missing registrations
            unsupported_vendor_error = ""

    return {
        "openai_text": openai_text,
        "anthropic_text": anthropic_text,
        "unsupported_vendor_error": unsupported_vendor_error,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the offline example and print the application-facing contract."""
    del argv
    result = run_demo()
    print(f"OPENAI_TEXT={result['openai_text']}")
    print(f"ANTHROPIC_TEXT={result['anthropic_text']}")
    print(f"OPENAI_TYPE={type(result['openai_text']).__name__}")
    print(f"ANTHROPIC_TYPE={type(result['anthropic_text']).__name__}")
    print(f"UNSUPPORTED_VENDOR_ERROR={result['unsupported_vendor_error']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
