#!/usr/bin/env python3
"""
Main command-line entry point for Mêtis.

Available subcommands:
  prompt  Send a prompt through the model pipeline
  dsl     Parse a minimal [key: value] DSL and print JSON
  worker  Run background task processing
  tasks   Inspect scheduled background tasks

Environment defaults (used for model selection):
  METIS_VENDOR (default: "mock")
  METIS_MODEL  (default: "stub")
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from metis.cli.tasks import handle_tasks_list, handle_tasks_show
from metis.cli.worker import handle_worker_run
from metis.components.model_manager import ModelManager
from metis.conversation_engine import ConversationEngine
from metis.dsl import DslError, interpret_prompt_dsl
from metis.dsl.lexer import lex
from metis.dsl.parser import Parser
from metis.models.model_factory import ModelFactory
from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder


# --------------------------------------------------------------------------- #
# Custom ArgumentParser to normalize error output for tests
# --------------------------------------------------------------------------- #


class _Parser(argparse.ArgumentParser):
    """
    Small parser subclass that normalizes CLI error messages.

    This keeps output stable for tests while still behaving like a normal
    argparse-based command-line application.
    """

    def error(self, message: str) -> None:
        """
        Override default error formatting to include a capitalized 'Error:'
        and a friendlier message for invalid prompt type choices.
        """
        friendly = message
        if "invalid choice" in message and "--type" in message:
            friendly = "Unknown prompt type. " + message

        # Print usage first, then exit with normalized error text.
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: Error: {friendly}\n")


# --------------------------------------------------------------------------- #
# Engine helper
# --------------------------------------------------------------------------- #


def _engine_from_env() -> ConversationEngine:
    """
    Build a ConversationEngine using environment variables for model selection.

    This keeps the CLI lightweight while still routing through the same
    model-management bridge used elsewhere in the system.
    """
    vendor = os.getenv("METIS_VENDOR", "mock")
    model = os.getenv("METIS_MODEL", "stub")

    client = ModelFactory.for_role(
        "analysis",
        {"vendor": vendor, "model": model, "policies": {}},
    )
    return ConversationEngine(model_manager=ModelManager(client))


# --------------------------------------------------------------------------- #
# Prompt DSL
# --------------------------------------------------------------------------- #


def parse_bracket_dsl(dsl_text: str) -> Dict[str, Any]:
    """Compatibility wrapper around the package's canonical interpreter."""
    return dict(interpret_prompt_dsl(dsl_text))


def _report_dsl_error(exc: DslError) -> int:
    print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 2


# --------------------------------------------------------------------------- #
# Subcommand handlers
# --------------------------------------------------------------------------- #


def handle_prompt(args: argparse.Namespace) -> int:
    """
    Execute a prompt end-to-end via the model pipeline.

    The command echoes the original input and then prints the model response.
    This keeps the CLI both human-friendly and stable for tests.
    """
    try:
        dsl_ctx = parse_bracket_dsl(getattr(args, "dsl", "") or "")
    except DslError as exc:
        return _report_dsl_error(exc)

    engine = _engine_from_env()
    context = getattr(args, "context", "") or ""

    # Compose a deterministic prompt so tests can assert on stable output.
    composed = args.input
    if context:
        composed += f"\n[Context] {context}"
    if dsl_ctx:
        composed += f"\n[DSL] {json.dumps(dsl_ctx, ensure_ascii=False)}"

    response = engine.generate_with_model(composed)

    print(args.input)
    print(response)
    return 0


def handle_dsl(args: argparse.Namespace) -> int:
    """
    Parse DSL and print a flat JSON object.

    Example output:
      {"persona":"Research Assistant","task":"Summarize","length":"3 bullet points"}
    """
    try:
        parsed = parse_bracket_dsl(args.input)
        if not args.show_stages:
            print(json.dumps(parsed, ensure_ascii=False))
            return 0

        tokens = lex(args.input)
        expressions = Parser(tokens).parse()
        prompt = DefaultPromptBuilder().build_with_context(parsed).render()
        result = {
            "source": args.input,
            "tokens": [token.type.name for token in tokens],
            "expressions": [type(expression).__name__ for expression in expressions],
            "context": parsed,
            "prompt": prompt,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except DslError as exc:
        return _report_dsl_error(exc)
    return 0


# --------------------------------------------------------------------------- #
# CLI wiring
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    """
    Build the top-level CLI parser and register all subcommands.
    """
    parser = _Parser(prog="metis-cli", description="Mêtis command-line tools")
    sub = parser.add_subparsers(dest="command", required=True)

    # prompt
    p_prompt = sub.add_parser("prompt", help="Send a prompt through the model pipeline")
    p_prompt.add_argument("--type", choices=["summarize", "plan", "translate", "greet"], required=True)
    p_prompt.add_argument("--input", required=True, help="User input text")
    p_prompt.add_argument("--context", default="", help="Optional extra context")
    p_prompt.add_argument("--dsl", default="", help="Optional [key: value] bracket DSL")
    p_prompt.set_defaults(func=handle_prompt)

    # dsl
    p_dsl = sub.add_parser("dsl", help="Parse a bracket DSL and output JSON")
    p_dsl.add_argument("--input", required=True, help="Bracket DSL like: [task: Summarize][length: short]")
    p_dsl.add_argument(
        "--show-stages",
        action="store_true",
        help="Show tokens, expression classes, context, and the built prompt",
    )
    p_dsl.set_defaults(func=handle_dsl)

    # worker
    p_worker = sub.add_parser("worker", help="Run background task processing")
    worker_sub = p_worker.add_subparsers(dest="worker_command", required=True)

    p_worker_run = worker_sub.add_parser("run", help="Process due background tasks once")
    p_worker_run.set_defaults(func=handle_worker_run)

    # tasks
    p_tasks = sub.add_parser("tasks", help="Inspect scheduled background tasks")
    tasks_sub = p_tasks.add_subparsers(dest="tasks_command", required=True)

    p_tasks_list = tasks_sub.add_parser("list", help="List scheduled tasks")
    p_tasks_list.set_defaults(func=handle_tasks_list)

    p_tasks_show = tasks_sub.add_parser("show", help="Show one scheduled task")
    p_tasks_show.add_argument("--id", required=True, help="Task identifier")
    p_tasks_show.set_defaults(func=handle_tasks_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Parse CLI arguments and dispatch to the selected subcommand handler.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
