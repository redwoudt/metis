"""Schedule and complete one background task without waiting in real time."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from metis.commands.base import ToolContext
from metis.commands.schedule import ScheduleTaskCommand
from metis.scheduling.clock import TestClock
from metis.scheduling.scheduler import InMemoryTaskScheduler
from metis.scheduling.worker import Worker


def run_demo(delay_minutes: int = 5) -> dict[str, Any]:
    """Schedule a task, advance a test clock, and execute the due work."""
    if delay_minutes < 1:
        raise ValueError("delay_minutes must be at least 1")

    clock = TestClock(datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    services = SimpleNamespace(clock=clock, scheduler=scheduler)

    command = ScheduleTaskCommand()
    result = command.execute(
        ToolContext(
            command=command,
            user="reader-10",
            args={
                "description": "Generate the weekly project summary",
                "time": f"in {delay_minutes} minutes",
            },
            services=services,
        )
    )

    worker = Worker(scheduler=scheduler, clock=clock)
    due_before = len(worker.run_once())
    clock.advance(minutes=delay_minutes)
    processed = worker.run_once()
    task = scheduler.get(result["task_id"])

    return {
        "task_id": result["task_id"],
        "scheduled_for": result["scheduled_for"],
        "status_before": result["status"],
        "due_before": due_before,
        "processed_after_advance": len(processed),
        "status_after": task.status if task is not None else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay-minutes", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_demo(args.delay_minutes)
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
