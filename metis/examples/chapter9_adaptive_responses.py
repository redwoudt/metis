"""Compare response strategies and decorators without calling a provider."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

from metis.response.generation.selector import (
    StrategySelector,
    available_response_styles,
)
from metis.response.rendering.composer import ResponseComposer


@dataclass
class RecordingModel:
    """Return stable text while recording the selected generation parameters."""

    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append((prompt, dict(kwargs)))
        return "Odysseus chooses the clearest course home."


def build_response(
    style: str,
    *,
    format_markdown: bool = False,
    include_citations: bool = False,
) -> tuple[dict[str, Any], str]:
    """Select a strategy, generate once, and decorate the returned text."""
    model = RecordingModel()
    strategy = StrategySelector().select({"style": style}, {})

    raw = strategy.generate(
        model,
        "Describe a careful route to Ithaca.",
    )

    response = ResponseComposer().compose(
        raw,
        {
            "format_markdown": format_markdown,
            "include_citations": include_citations,
        },
    )

    return model.calls[0][1], response.render()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--style",
        choices=sorted(available_response_styles()),
        default="concise",
    )
    parser.add_argument("--format-markdown", action="store_true")
    parser.add_argument("--include-citations", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    parameters, response = build_response(
        args.style,
        format_markdown=args.format_markdown,
        include_citations=args.include_citations,
    )

    print(f"style={args.style}")
    print(f"generation={parameters}")
    print(response)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())