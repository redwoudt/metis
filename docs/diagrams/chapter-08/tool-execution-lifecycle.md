# Chapter 8 governed tool execution

This diagram expands the simplified sequence used for Figure 8.3 in Chapter 8.
It follows one selected tool from the conversation lifecycle through allow-listed
lookup, policy selection, the handler chain, command execution, lifecycle events,
and result recording.

The chapter groups several of these responsibilities so that the printed figure
remains legible. This repository version preserves the implementation detail.

## Detailed sequence

```mermaid
sequenceDiagram
    autonumber

    actor Caller
    participant Mediator as ConversationMediator
    participant State as ConversationEngine / ExecutingState
    participant Events as EventBus
    participant Executor as ToolExecutor
    participant Registry as Command registry
    participant Pipeline as Handler pipeline
    participant Command as ToolCommand / receiver

    Caller->>Mediator: Submit request with selected tool
    Mediator->>State: respond(clean_input)
    State->>Events: Publish command.started
    State->>Executor: execute_tool(name, args, user, correlation_id)
    Executor->>Registry: Resolve the allow-listed tool name

    alt Tool name is unknown
        Registry-->>Executor: No matching command
        Executor--xState: ToolExecutionError
        State->>Events: Publish command.failed
        State--xMediator: Re-raise the error
        Mediator--xCaller: Request fails visibly
    else Command is registered
        Registry-->>Executor: Command class
        Executor->>Command: Create command instance
        Executor->>Executor: Build ToolContext and read execution_policy

        alt Strict policy
            Executor->>Pipeline: Validation, permission, quota, audit, execution
        else Light policy
            Executor->>Pipeline: Validation and execution
        end

        alt A handler rejects the request
            Pipeline--xExecutor: Validation or policy error
            Executor--xState: Propagate the error
            State->>Events: Publish command.failed
            State--xMediator: Re-raise the error
            Mediator--xCaller: Request fails visibly
        else The handler chain approves execution
            Pipeline->>Command: execute(context)
            Command-->>Pipeline: Store result in ToolContext
            Pipeline-->>Executor: Completed ToolContext
            Executor-->>State: Return result
            State->>Events: Publish command.completed
            State->>State: Store tool output and inspection record
            State->>State: Generate narration and enter SummarizingState
            State-->>Mediator: Executing response
            Mediator-->>Caller: Response and execution evidence
        end
    end
```

## Reading the diagram

- `ConversationMediator` coordinates the request and delegates the active turn
  to the conversation engine. It does not execute the tool itself.
- `ExecutingState` publishes lifecycle events, calls the injected
  `ToolExecutor`, records the outcome, and moves the conversation to
  `SummarizingState` after successful execution.
- `ToolExecutor` treats the proposed tool name only as an allow-listed registry
  key. It creates the command and `ToolContext`, then selects the command's
  declared `light` or `strict` execution policy.
- The light pipeline contains validation and execution. The strict pipeline
  adds permission, rate-limit, and audit handlers before execution.
- An unknown tool or any handler failure stops the sequence before the command
  can produce a side effect. The exception remains visible to the caller.
- On success, the command result returns through `ToolContext`; the state stores
  the output, publishes `command.completed`, records inspection evidence, and
  prepares narration for the next state.

## Scope

The diagram shows the runtime responsibilities relevant to Command and Chain of
Responsibility. It groups the individual handler objects under `Handler
pipeline` and combines the concrete command with its receiver. It intentionally
omits prompt rendering details, model-adapter selection, session persistence,
checkpointing, and response decoration, which are covered in other chapters.

## Related implementation

- [`ConversationMediator`](../../../metis/mediator/conversation_mediator.py)
- [`ExecutingState`](../../../metis/states/executing.py)
- [`ToolExecutor`](../../../metis/tools/tool_executor.py)
- [`ToolCommand` and `ToolContext`](../../../metis/commands/base.py)
- [Built-in command registry](../../../metis/commands/__init__.py)
- [Light and strict pipelines](../../../metis/handlers/pipelines.py)
- [Handler implementations](../../../metis/handlers)
- [`ExecuteSQLCommand`](../../../metis/commands/sql.py)
- [Provider-free Chapter 8 example](../../../metis/examples/chapter8_governed_tools.py)

## Focused verification

- [`test_chapter8_governed_tools.py`](../../../tests/examples/test_chapter8_governed_tools.py)
- [`test_tool_executor.py`](../../../tests/tools/test_tool_executor.py)
- [`test_validation_handler.py`](../../../tests/handlers/test_validation_handler.py)
- [`test_permission_handler.py`](../../../tests/handlers/test_permission_handler.py)
- [`test_ratelimit_handler.py`](../../../tests/handlers/test_ratelimit_handler.py)
- [`test_auditlog_handler.py`](../../../tests/handlers/test_auditlog_handler.py)
- [`test_execute_command_handler.py`](../../../tests/handlers/test_execute_command_handler.py)
- [`test_executing_state.py`](../../../tests/state/test_executing_state.py)
- [`test_executing_state_events.py`](../../../tests/state/test_executing_state_events.py)

Run the provider-free example and focused tests from the repository root:

```sh
python -m metis.examples.chapter8_governed_tools --city Ithaca
python -m metis.examples.chapter8_governed_tools --city Ithaca --deny
pytest tests/examples/test_chapter8_governed_tools.py \
  tests/tools/test_tool_executor.py \
  tests/handlers/test_validation_handler.py \
  tests/handlers/test_permission_handler.py \
  tests/handlers/test_ratelimit_handler.py \
  tests/handlers/test_auditlog_handler.py \
  tests/handlers/test_execute_command_handler.py \
  tests/state/test_executing_state.py \
  tests/state/test_executing_state_events.py
```
