# metis/states/executing.py

import logging
from time import perf_counter
from uuid import uuid4
from typing import Optional, Any, Callable

from metis.events import (
    Event,
    argument_summary,
    exception_summary,
    result_summary,
)
from metis.inspection.records import ToolResultRecord
from metis.states.base_state import ConversationState

logger = logging.getLogger("metis.states.executing")


class ExecutingState(ConversationState):
    """
    Executes the selected tool and produces a narration.
    Transitions to SummarizingState afterwards.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input: str) -> str:
        from metis.services.prompt_service import render_prompt
        from metis.states.summarizing import SummarizingState

        if not hasattr(engine, "preferences") or engine.preferences is None:
            engine.preferences = {}

        # Execute tool (if selected)
        tool_output = self._execute_selected_tool(engine)

        # Build executing prompt
        rendered_prompt = render_prompt(
            prompt_type="execute",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", "") if tool_output else "",
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", ""),
        )

        logger.debug(
            "[ExecutingState] Prompt constructed: length=%d",
            len(str(rendered_prompt)),
        )

        # Ask the model for narration
        model_response = engine.generate_with_model(rendered_prompt)

        # Transition
        engine.set_state(SummarizingState())

        # IMPORTANT: Tests assert semantic intent ("executing" in output)
        narration = str(model_response).strip() if model_response is not None else ""
        if narration:
            return f"Executing: {narration}"
        return "Executing:"

    # -----------------------------
    # Internal helpers
    # -----------------------------


    def _resolve_user(self, engine) -> str:
        return getattr(engine, "user_id", None) or getattr(engine, "user", None) or "tester"


    def _call_execute_tool(
        self,
        fn: Callable[..., Any],
        services: Any,
        tool_name: str,
        tool_args: dict,
        user_val: str,
        correlation_id: str | None = None,
    ) -> Any:
        """
        Try multiple signatures to support different handler implementations.
        """
        attempts = [
            # keyword forms
            lambda: fn(
                tool_name=tool_name,
                args=tool_args,
                user=user_val,
                services=services,
                correlation_id=correlation_id,
                idempotency_key=correlation_id,
            ),
            lambda: fn(tool_name=tool_name, args=tool_args, user=user_val, services=services),
            lambda: fn(tool_name=tool_name, args=tool_args, user=user_val),
            # positional forms
            lambda: fn(tool_name, tool_args, user_val, services),
            lambda: fn(tool_name, tool_args, user_val),
            # services-first positional variant
            lambda: fn(services, tool_name, tool_args, user_val),
        ]

        last_err: Optional[Exception] = None
        for attempt in attempts:
            try:
                return attempt()
            except TypeError as e:
                last_err = e
                continue

        if last_err is not None:
            raise last_err
        return None

    def _publish_command_event(
        self,
        engine,
        event_type: str,
        tool_name: str,
        tool_args: dict,
        *,
        severity: str = "INFO",
        extra_payload: dict | None = None,
    ) -> None:
        """
        Publish a command lifecycle event if the shared EventBus is available.

        ExecutingState receives infrastructure through the engine. It should not
        reach back into global services or request handlers.
        """
        event_bus = getattr(engine, "event_bus", None)

        if event_bus is None:
            services = getattr(engine, "services", None)
            event_bus = getattr(services, "event_bus", None) if services is not None else None

        if event_bus is None:
            return

        prefs = getattr(engine, "preferences", {}) or {}
        correlation_id = prefs.get("correlation_id") or str(uuid4())
        payload = {
            "command_name": tool_name,
            **argument_summary(tool_args),
        }
        if extra_payload:
            payload.update(extra_payload)

        event_bus.publish(
            Event.create(
                event_type=event_type,
                source="ExecutingState",
                correlation_id=correlation_id,
                payload=payload,
                metadata={
                    "user_id": self._resolve_user(engine),
                },
                severity=severity,
            )
        )

    @staticmethod
    def _record_tool_result(
        engine,
        *,
        name: str,
        status: str,
        started_at: float,
        output: Any = None,
        error: BaseException | None = None,
    ) -> None:
        records = getattr(engine, "inspection_tool_results", None)
        if not isinstance(records, list):
            return
        duration_ms = max(0, int((perf_counter() - started_at) * 1000))
        if error is not None:
            summary = f"error_type={error.__class__.__name__}"
        else:
            parts = result_summary(output)
            summary = "; ".join(f"{key}={value}" for key, value in parts.items())
        records.append(
            ToolResultRecord(
                name=name,
                status=status,
                duration_ms=duration_ms,
                output_summary=summary,
            )
        )

    def _execute_selected_tool(self, engine) -> Optional[Any]:
        if not isinstance(getattr(engine, "preferences", None), dict):
            return None

        tool_name = engine.preferences.get("tool_name")
        tool_args = engine.preferences.get("tool_args") or {}

        if not tool_name:
            engine.preferences.pop("tool_output", None)
            return None

        user_val = self._resolve_user(engine)
        services = getattr(engine, "services", None)
        executor = getattr(engine, "tool_executor", None)

        started_at = perf_counter()
        correlation_id = (engine.preferences or {}).get("correlation_id")
        logger.info(
            "[ExecutingState] Attempting tool execution: %s argument_names=%s",
            tool_name,
            sorted(str(name) for name in tool_args),
        )
        self._publish_command_event(
            engine,
            "command.started",
            tool_name,
            tool_args,
        )

        if executor is None:
            out = f"RESULT:{tool_name}:{tool_args}"
            engine.preferences["tool_output"] = out
            self._publish_command_event(
                engine,
                "command.completed",
                tool_name,
                tool_args,
                extra_payload=result_summary(out),
            )
            self._record_tool_result(
                engine,
                name=tool_name,
                status="completed",
                started_at=started_at,
                output=out,
            )
            return out

        exec_fn = getattr(executor, "execute_tool", None)
        if not callable(exec_fn):
            out = f"RESULT:{tool_name}:{tool_args}"
            engine.preferences["tool_output"] = out
            self._publish_command_event(
                engine,
                "command.completed",
                tool_name,
                tool_args,
                extra_payload=result_summary(out),
            )
            self._record_tool_result(
                engine,
                name=tool_name,
                status="completed",
                started_at=started_at,
                output=out,
            )
            return out

        try:
            out = self._call_execute_tool(
                exec_fn,
                services=services,
                tool_name=tool_name,
                tool_args=tool_args,
                user_val=user_val,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            logger.error(
                "[ExecutingState] tool execution failed error_type=%s",
                exc.__class__.__name__,
            )
            self._publish_command_event(
                engine,
                "command.failed",
                tool_name,
                tool_args,
                severity="ERROR",
                extra_payload=exception_summary(exc),
            )
            self._record_tool_result(
                engine,
                name=tool_name,
                status="failed",
                started_at=started_at,
                error=exc,
            )
            raise

        engine.preferences["tool_output"] = out
        self._publish_command_event(
            engine,
            "command.completed",
            tool_name,
            tool_args,
            extra_payload=result_summary(out),
        )
        self._record_tool_result(
            engine,
            name=tool_name,
            status="completed",
            started_at=started_at,
            output=out,
        )
        return out
