from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from metis.components.session_manager import SessionManager
from metis.handler import RequestHandler
from metis.memory.manager import MemoryManager
from metis.scheduling.scheduler import BackgroundCommand, TaskStatus
from metis.services.services import Services
from metis.states.executing import ExecutingState


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


@pytest.fixture
def workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("METIS_TASK_SCHEDULER", "inmemory")
    services = Services(plugin_config={"enabled_plugins": (), "strict_plugins": True})
    observer = SpyObserver()
    services.event_bus.subscribe_all(observer)
    memory = MemoryManager(file_path=str(tmp_path / "snapshots.pkl"))
    handler = RequestHandler(
        services=services,
        session_manager=SessionManager(file_path=str(tmp_path / "sessions.pkl")),
        memory_manager=memory,
        config={"vendor": "mock", "model": "chapter18", "policies": {}},
    )
    return handler, services, memory, observer


def test_request_result_is_scoped_correlated_and_private(workflow):
    handler, _, _, observer = workflow
    secret = "chapter18-secret-prompt"

    result = handler.run("reader-18", f"[tone:concise] {secret}")

    assert result.response
    assert "[Tone: concise]" in result.response
    assert result.execution_trace.correlation_id == result.correlation_id
    assert result.execution_trace.prompt_plan.sections[0].content == ""
    assert result.execution_trace.response.content == ""
    assert result.execution_trace.model_call.provider == "mock"
    assert result.execution_trace.model_call.model == "chapter18"

    request_events = [
        event
        for event in observer.events
        if event.correlation_id == result.correlation_id
    ]
    prompt_event = next(
        event for event in request_events if event.event_type == "prompt.received"
    )
    assert prompt_event.payload["content_length"] == len(f"[tone:concise] {secret}")
    assert len(prompt_event.payload["content_sha256"]) == 64
    assert secret not in repr(
        [(event.payload, event.metadata) for event in request_events]
    )

    terminal_events = [
        event.event_type
        for event in request_events
        if event.event_type in {"response.generated", "response.failed"}
    ]
    assert terminal_events == ["response.generated"]


def test_checkpoints_are_saved_after_success_and_isolated_by_user(workflow):
    handler, _, memory, _ = workflow

    saved = handler.run("odysseus", "Remember this turn", save=True)

    assert saved.checkpoint_saved is True
    assert memory.count(scope="odysseus") == 1
    assert memory.count(scope="polyphemus") == 0

    with pytest.raises(LookupError, match="No checkpoint"):
        handler.run("polyphemus", "Try another user's checkpoint", undo=True)

    restored = handler.run("odysseus", "Continue from the checkpoint", undo=True)

    assert restored.checkpoint_restored is True
    assert memory.count(scope="odysseus") == 0


def test_tool_execution_records_safe_request_scoped_trace(workflow):
    handler, services, _, _ = workflow
    sensitive_result = "private-tool-result"

    def execute_tool(**kwargs):
        return {"answer": sensitive_result}

    services.tool_executor.execute_tool = execute_tool
    session = handler.session_manager.load_or_create("tool-user")
    session.engine.set_state(ExecutingState())
    session.engine._explicit_state = True
    session.engine.preferences.update(
        {
            "tool_name": "search_web",
            "tool_args": {"query": "private-query"},
        }
    )

    result = handler.run("tool-user", "Run the selected tool")

    command = result.execution_trace.tool_commands[0]
    tool_result = result.execution_trace.tool_results[0]
    assert command.name == "search_web"
    assert command.args == {"query": "<redacted>"}
    assert tool_result.status == "completed"
    assert sensitive_result not in tool_result.output_summary
    assert "result_keys=['answer']" in tool_result.output_summary


def test_background_tool_uses_owning_runtime_and_carries_identities(workflow):
    _, services, _, observer = workflow
    calls = []

    def execute_tool(**kwargs):
        calls.append(kwargs)
        return {"ok": True}

    services.tool_executor.execute_tool = execute_tool
    task = BackgroundCommand(
        description="Deferred Chapter 18 tool",
        scheduled_for=services.clock.now(),
        task_type="tool_command",
        created_by="worker-user",
        payload={
            "tool_name": "search_web",
            "args": {"query": "workflow"},
            "user": "worker-user",
            "correlation_id": "request-18",
            "idempotency_key": "effect-18",
        },
    )
    services.scheduler.schedule(task)

    processed = services.worker.run_once()

    assert processed == [task]
    assert task.status == TaskStatus.COMPLETED
    assert calls[0]["services"] is services
    assert calls[0]["correlation_id"] == "request-18"
    assert calls[0]["idempotency_key"] == "effect-18"
    task_events = [
        event for event in observer.events if event.event_type.startswith("task.")
    ]
    assert {event.event_type for event in task_events} == {
        "task.started",
        "task.completed",
    }
    assert {event.correlation_id for event in task_events} == {"request-18"}


def test_model_failure_has_one_terminal_truth_without_sensitive_message(
    workflow,
):
    handler, services, _, observer = workflow
    secret = "provider-secret-message"

    class FailingModel:
        provider = "test"
        model = "failure"

        def generate(self, prompt, **kwargs):
            raise RuntimeError(secret)

    handler.mediator.model_resolver = lambda role, config: FailingModel()

    with pytest.raises(RuntimeError, match=secret):
        handler.run("failure-user", "Trigger a model failure")

    request_events = [
        event
        for event in observer.events
        if event.metadata.get("user_id") == "failure-user"
        or event.event_type.startswith("model.")
    ]
    event_types = [event.event_type for event in request_events]
    assert "model.failed" in event_types
    assert "response.failed" in event_types
    assert "response.generated" not in event_types
    assert secret not in repr([event.payload for event in request_events])
    assert {event.correlation_id for event in request_events} == {
        request_events[0].correlation_id
    }


def test_importing_services_has_no_runtime_side_effects(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root)
    code = (
        "from pathlib import Path; "
        "import metis.services.services as module; "
        "assert module._services_singleton is None; "
        "assert not Path('.metis').exists()"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
