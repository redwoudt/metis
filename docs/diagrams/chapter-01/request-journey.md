# Chapter 1 request journey

This is the compact request sequence used in Chapter 1. It introduces the
ownership boundaries without asking a first-time reader to follow every
runtime component. The diagram groups policy, session, model, and tool work as
runtime collaborators, and groups the event bus, checkpoint memory, and
session storage as evidence and storage.

## Simplified sequence

```mermaid
sequenceDiagram
    autonumber

    actor Caller
    participant Handler as RequestHandler
    participant Mediator as ConversationMediator
    participant Runtime as Runtime collaborators
    participant Evidence as Evidence and storage

    Caller->>Handler: Submit prompt
    Handler->>Mediator: Delegate request
    Mediator->>Evidence: Publish prompt.received
    Mediator->>Runtime: Apply policy, load session, and resolve behavior
    Runtime-->>Mediator: Governed request context
    Mediator->>Runtime: Execute the conversation turn
    Runtime-->>Mediator: Response and inspection records

    opt Save requested
        Mediator->>Evidence: Save checkpoint
    end

    Mediator->>Mediator: Build immutable execution trace
    Mediator->>Evidence: Persist session and publish response.generated
    Mediator-->>Handler: RequestResult or response text
    Handler-->>Caller: Return result

    Note over Mediator,Evidence: On error, publish response.failed and re-raise
```

## Reading the diagram

- `RequestHandler` is the caller-facing Facade. It keeps the public entry point
  stable and delegates the lifecycle.
- `ConversationMediator` owns the sequence. It coordinates the request without
  absorbing the specialist behavior behind policy, state, model, tool, event,
  or persistence boundaries.
- Runtime collaborators represent the policy, session, behavior, model, tool,
  and conversation-engine components used during a request.
- Evidence and storage represent the event bus, checkpoint memory, and session
  persistence. These are grouped only to keep the chapter figure legible.
- A successful request creates any requested checkpoint, builds the immutable
  execution trace, persists the session, publishes the terminal success event,
  and returns a request-scoped result.

## Scope

The diagram intentionally omits the detailed `undo` path, prompt DSL parsing,
model and tool selection, response-strategy configuration, individual event
types, and the full failure branch. See the
[Chapter 2 request lifecycle](../chapter-02/request-lifecycle.md) for the
expanded sequence and [Chapter 18 full workflow](../../full_workflow.md) for
the end-to-end architecture.

## Related implementation

- [`RequestHandler`](../../../metis/handler/request_handler.py)
- [`ConversationMediator`](../../../metis/mediator/conversation_mediator.py)
- [`RequestContext`](../../../metis/mediator/context.py)
- [`RequestResult`](../../../metis/mediator/result.py)
- [`examples/run_request.py`](../../../examples/run_request.py)

## Focused verification

- [`test_conversation_mediator_lifecycle.py`](../../../tests/mediator/test_conversation_mediator_lifecycle.py)
- [`test_request_handler_response_wiring.py`](../../../tests/handler/test_request_handler_response_wiring.py)
- [`test_request_handler_events.py`](../../../tests/handler/test_request_handler_events.py)

