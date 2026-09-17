"""Compare Builder and Template Method prompt construction without a provider."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder
from metis.prompts.prompt import Prompt
from metis.prompts.templates.planning_prompt import PlanningPrompt


PLANNING_TASK = "Create a step-by-step plan based on the provided information."


def build_with_builder(
    user_input: str,
    *,
    context: str,
    tool_output: str,
    tone: str,
    persona: str,
) -> Prompt:
    """Assemble one prompt explicitly through the fluent Builder API."""
    return (
        DefaultPromptBuilder()
        .add_tone(tone, persona)
        .add_task_instruction(PLANNING_TASK)
        .add_context(context)
        .add_tool_output(tool_output)
        .set_user_input(user_input)
        .build()
    )


def build_with_template(
    user_input: str,
    *,
    context: str,
    tool_output: str,
    tone: str,
    persona: str,
) -> Prompt:
    """Build the same prompt through PlanningPrompt's fixed sequence."""
    template = PlanningPrompt(
        context=context,
        tool_output=tool_output,
        tone=tone,
        persona=persona,
    )
    return template.build_prompt(user_input)


def compare_prompt_paths(
    user_input: str,
    *,
    context: str,
    tool_output: str,
    tone: str = "Supportive",
    persona: str = "Step-by-Step Coach",
) -> tuple[str, str]:
    """Return rendered prompts from the two construction paths."""
    common = {
        "context": context,
        "tool_output": tool_output,
        "tone": tone,
        "persona": persona,
    }
    builder_text = build_with_builder(user_input, **common).render()
    template_text = build_with_template(user_input, **common).render()
    return builder_text, template_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="Help me prepare for an AI architecture interview.",
    )
    parser.add_argument(
        "--context",
        default="The interview is in two weeks.",
    )
    parser.add_argument(
        "--tool-output",
        default="Calendar: five open study slots each week.",
    )
    parser.add_argument("--tone", default="Supportive")
    parser.add_argument("--persona", default="Step-by-Step Coach")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    builder_text, template_text = compare_prompt_paths(
        args.input,
        context=args.context,
        tool_output=args.tool_output,
        tone=args.tone,
        persona=args.persona,
    )
    matches = builder_text == template_text

    print("BUILDER")
    print(builder_text)
    print("\nTEMPLATE METHOD")
    print(template_text)
    print(f"\nMATCH={matches}")
    return 0 if matches else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
