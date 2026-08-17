"""Compare Mêtis behavior templates without calling a model provider."""

import argparse

from metis.behavior import BehaviorContext, build_default_behavior_strategy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--behavior", default="balanced")
    parser.add_argument("--risk", choices=("normal", "high"), default="normal")
    args = parser.parse_args()

    strategy = build_default_behavior_strategy({})
    plan = strategy.choose(
        BehaviorContext(requested_template=args.behavior, risk=args.risk)
    )
    print(f"template={plan.name}")
    print(f"model_role={plan.model_role}")
    print(f"response_style={plan.response_style}")
    print(f"allow_tools={plan.allow_tools}")
    print(f"safety={plan.require_safety}")
    print(f"citations={plan.include_citations}")


if __name__ == "__main__":
    main()
