# Chapter 18: Full GenAI Workflow

Chapter 18 joins the existing Mêtis patterns into one request lifecycle. The
`RequestHandler` remains the public façade, `ConversationMediator` owns the
ordering, and `Services` supplies one frozen runtime graph shared by foreground
requests and background workers.

## Request lifecycle

```mermaid
flowchart LR
    A["RequestHandler.run"] --> B["Policy and DSL"]
    B --> C["Behavior, tool, and model selection"]
    C --> D["State and prompt construction"]
    D --> E["Model and tool execution"]
    E --> F["Response rendering"]
    F --> G["Checkpoint, trace, and events"]
    G --> H["RequestResult"]
```

Use `handle_prompt` when an existing caller needs only response text. Use `run`
when the caller also needs the correlation ID, completed execution trace, or
checkpoint outcome:

```python
result = handler.run("user-42", "Explain the workflow", save=True)
print(result.response)
print(result.correlation_id)
result.execution_trace.accept(visitor)
```

The returned `RequestResult` is immutable and request-scoped. Callers do not
need to read mutable `last_*` fields from a shared mediator.

## Operational guarantees

- Each lifecycle event carries the same request correlation ID.
- Exported events contain lengths, hashes, argument names, result shape, and
  error type—not raw prompts, argument values, results, or exception messages.
- A request emits one terminal response event: `response.generated` or
  `response.failed`. Failures are re-raised to the caller.
- Checkpoints are saved only after a successful turn and are isolated by user
  scope. Restores retain the live model, event bus, tool executor, and services.
- Scheduled tool work executes through the same `Services` instance and frozen
  command registry that admitted it. Correlation and idempotency identities
  travel with the task.
- Importing `metis.services.services` creates no runtime container or SQLite
  database. The process-level container is initialized lazily on first use.

## Local example

The example uses the deterministic mock adapter and an in-memory scheduler, so
it requires no provider credentials or network access:

```sh
python -m metis.examples.chapter18_full_workflow
```
