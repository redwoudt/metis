from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List
from uuid import uuid4
import json
import re
import sqlite3

from .clock import Clock


class TaskStatus:
    """
    Lightweight status constants for background task lifecycle.
    """

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"


@dataclass
class BackgroundCommand:
    """
    Durable unit of scheduled work.

    A background task is a transport object that carries execution metadata,
    lifecycle state, and a payload describing what should happen later.
    The actual execution logic may be provided either by the task itself or
    delegated to a task executor registry.

    Important fields:
    - description: human-readable summary of the task
    - scheduled_for: when the task becomes eligible for execution
    - task_type: logical category used for executor dispatch
    - retries/max_retries: failure recovery tracking
    - status: lifecycle tracking
    - payload: structured task-specific execution data
    """

    description: str
    scheduled_for: datetime
    task_type: str = "generic"
    id: str = field(default_factory=lambda: str(uuid4()))
    retries: int = 0
    max_retries: int = 3
    status: str = TaskStatus.SCHEDULED
    created_by: Any = None
    last_error: str | None = None
    result: Any = None
    payload: dict[str, Any] = field(default_factory=dict)

    def execute(self, context: Any = None) -> Any:
        """
        Backwards-compatible fallback execution.

        This keeps the task model usable even when no executor registry is
        configured. More advanced task types can instead be dispatched through
        a dedicated executor registry owned by the worker.
        """
        return {
            "delivered": True,
            "description": self.description,
            "task_type": self.task_type,
            "payload": dict(self.payload),
        }


class TaskScheduler(ABC):
    """
    Abstract scheduler interface.
    """

    @abstractmethod
    def schedule(self, command: BackgroundCommand) -> BackgroundCommand:
        raise NotImplementedError

    @abstractmethod
    def next_due_tasks(self, now: datetime) -> List[BackgroundCommand]:
        raise NotImplementedError

    @abstractmethod
    def save(self, command: BackgroundCommand) -> BackgroundCommand:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: str) -> BackgroundCommand | None:
        raise NotImplementedError

    @abstractmethod
    def all_tasks(self) -> List[BackgroundCommand]:
        raise NotImplementedError


class InMemoryTaskScheduler(TaskScheduler):
    """
    In-memory scheduler implementation for tests and lightweight flows.
    """

    def __init__(self, clock: Clock | None = None):
        self.clock = clock or Clock()
        self._tasks: dict[str, BackgroundCommand] = {}

    def schedule(self, command: BackgroundCommand) -> BackgroundCommand:
        command.status = TaskStatus.SCHEDULED
        self._tasks[command.id] = command
        return command

    def next_due_tasks(self, now: datetime | None = None) -> List[BackgroundCommand]:
        now = now or self.clock.now()
        return [
            task
            for task in self._tasks.values()
            if task.status == TaskStatus.SCHEDULED and task.scheduled_for <= now
        ]

    def save(self, command: BackgroundCommand) -> BackgroundCommand:
        self._tasks[command.id] = command
        return command

    def get(self, task_id: str) -> BackgroundCommand | None:
        return self._tasks.get(task_id)

    def all_tasks(self) -> List[BackgroundCommand]:
        return list(self._tasks.values())


class SQLiteTaskScheduler(TaskScheduler):
    """
    SQLite-backed task scheduler.

    This scheduler persists tasks to a local SQLite database so that scheduled
    work survives process boundaries and can be inspected or executed by
    separate CLI invocations.
    """

    def __init__(self, db_path: str | Path, clock: Clock | None = None):
        self.clock = clock or Clock()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    retries INTEGER NOT NULL,
                    max_retries INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT,
                    last_error TEXT,
                    result TEXT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _to_row(self, command: BackgroundCommand) -> dict[str, Any]:
        return {
            "id": command.id,
            "description": command.description,
            "scheduled_for": command.scheduled_for.isoformat(),
            "task_type": command.task_type,
            "retries": command.retries,
            "max_retries": command.max_retries,
            "status": command.status,
            "created_by": json.dumps(command.created_by),
            "last_error": command.last_error,
            "result": json.dumps(command.result),
            "payload": json.dumps(command.payload),
        }

    def _from_row(self, row: sqlite3.Row) -> BackgroundCommand:
        return BackgroundCommand(
            id=row["id"],
            description=row["description"],
            scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
            task_type=row["task_type"],
            retries=row["retries"],
            max_retries=row["max_retries"],
            status=row["status"],
            created_by=json.loads(row["created_by"]) if row["created_by"] else None,
            last_error=row["last_error"],
            result=json.loads(row["result"]) if row["result"] else None,
            payload=json.loads(row["payload"]) if row["payload"] else {},
        )

    def schedule(self, command: BackgroundCommand) -> BackgroundCommand:
        command.status = TaskStatus.SCHEDULED
        return self.save(command)

    def save(self, command: BackgroundCommand) -> BackgroundCommand:
        row = self._to_row(command)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, description, scheduled_for, task_type, retries,
                    max_retries, status, created_by, last_error, result, payload
                )
                VALUES (
                    :id, :description, :scheduled_for, :task_type, :retries,
                    :max_retries, :status, :created_by, :last_error, :result, :payload
                )
                ON CONFLICT(id) DO UPDATE SET
                    description = excluded.description,
                    scheduled_for = excluded.scheduled_for,
                    task_type = excluded.task_type,
                    retries = excluded.retries,
                    max_retries = excluded.max_retries,
                    status = excluded.status,
                    created_by = excluded.created_by,
                    last_error = excluded.last_error,
                    result = excluded.result,
                    payload = excluded.payload
                """,
                row,
            )
            conn.commit()
        return command

    def get(self, task_id: str) -> BackgroundCommand | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def all_tasks(self) -> List[BackgroundCommand]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY scheduled_for ASC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def next_due_tasks(self, now: datetime | None = None) -> List[BackgroundCommand]:
        now = now or self.clock.now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status = ? AND scheduled_for <= ?
                ORDER BY scheduled_for ASC
                """,
                (TaskStatus.SCHEDULED, now.isoformat()),
            ).fetchall()
        return [self._from_row(row) for row in rows]


def parse_schedule_time(value: Any, now: datetime) -> datetime:
    """
    Best-effort parser for human-friendly schedule input.
    """
    if isinstance(value, datetime):
        return value

    if value is None:
        raise ValueError("Schedule task requires 'time'.")

    text = str(value).strip().lower()

    if text in {"now", "immediately", "today"}:
        return now

    if text == "tomorrow":
        return now + timedelta(days=1)

    match = re.fullmatch(
        r"in\s+(\d+)\s+(second|seconds|minute|minutes|hour|hours|day|days)",
        text,
    )
    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if unit.startswith("second"):
            return now + timedelta(seconds=amount)
        if unit.startswith("minute"):
            return now + timedelta(minutes=amount)
        if unit.startswith("hour"):
            return now + timedelta(hours=amount)
        return now + timedelta(days=amount)

    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(
            "Unsupported time format. Use a datetime, ISO string, 'tomorrow', or 'in N minutes'."
        ) from exc