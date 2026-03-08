"""
Worker-related CLI commands for Mêtis.

This module provides operational entry points for processing scheduled
background tasks outside the normal request-response flow.
"""

from __future__ import annotations

import argparse

from metis.services.services import get_services


def handle_worker_run(args: argparse.Namespace) -> int:
    """
    Process all tasks that are currently due and print a simple summary.

    This runs the worker once rather than starting a long-lived daemon. That
    keeps the behavior easy to test and makes it suitable for manual use,
    cron-based execution, or future process supervision.
    """
    services = get_services()
    processed = services.worker.run_once()

    print(f"Processed {len(processed)} task(s).")

    for task in processed:
        print(
            f"- id={task.id} "
            f"status={task.status} "
            f"description={task.description}"
        )

    return 0