from __future__ import annotations

import argparse
import json

from metis.services.services import get_services


def handle_tasks_list(args: argparse.Namespace) -> int:
    """
    List all scheduled tasks.
    """
    services = get_services()
    tasks = services.scheduler.all_tasks()

    rows = [
        {
            "id": task.id,
            "description": task.description,
            "task_type": task.task_type,
            "status": task.status,
            "scheduled_for": task.scheduled_for.isoformat(),
            "retries": task.retries,
            "max_retries": task.max_retries,
        }
        for task in tasks
    ]

    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def handle_tasks_show(args: argparse.Namespace) -> int:
    """
    Show one task by id.
    """
    services = get_services()
    task = services.scheduler.get(args.id)

    if task is None:
        print(json.dumps({"error": f"Task '{args.id}' not found."}, ensure_ascii=False))
        return 1

    print(
        json.dumps(
            {
                "id": task.id,
                "description": task.description,
                "task_type": task.task_type,
                "status": task.status,
                "scheduled_for": task.scheduled_for.isoformat(),
                "retries": task.retries,
                "max_retries": task.max_retries,
                "created_by": task.created_by,
                "last_error": task.last_error,
                "result": task.result,
                "payload": task.payload,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0