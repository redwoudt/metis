"""Compare real, null, and omitted event publishers for Chapter 15."""

from __future__ import annotations

import argparse

from metis.components.model_manager import ModelManager
from metis.events import Event, EventBus, NullEventPublisher
from metis.models.adapters.mock_adapter import MockAdapter


class EventCollector:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def notify(self, event: Event) -> None:
        self.events.append(event)


def build_manager(mode: str) -> tuple[ModelManager, EventCollector]:
    client = MockAdapter("chapter-15")
    collector = EventCollector()

    if mode == "real":
        publisher = EventBus()
        publisher.subscribe_all(collector)
        return ModelManager(client, event_bus=publisher), collector

    if mode == "null":
        return (
            ModelManager(client, event_bus=NullEventPublisher()),
            collector,
        )

    return ModelManager(client), collector


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare Chapter 15 event-publisher configurations."
    )
    parser.add_argument(
        "--publisher",
        choices=("real", "null", "omitted"),
        default="omitted",
    )
    parser.add_argument("--prompt", default="Continue")
    args = parser.parse_args()

    manager, collector = build_manager(args.publisher)
    response = manager.generate(args.prompt, correlation_id="chapter-15-demo")

    print(f"Configuration: {args.publisher}")
    print(f"Publisher: {type(manager.event_bus).__name__}")
    print(f"Events captured: {len(collector.events)}")
    print(f"Response: {response}")
    print("Core request: complete")


if __name__ == "__main__":
    main()
