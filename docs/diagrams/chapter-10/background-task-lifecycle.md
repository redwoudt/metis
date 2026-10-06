# Chapter 10 background-task lifecycle

This page contains the compact sequence used for Figure 10.3 in Chapter 10 and
a detailed component-level version for repository readers. Both diagrams show
the same lifetime boundary: the request returns after the task has been stored,
and a worker executes the stored work later through the runtime that owns it.

The compact figure groups request admission and scheduling under `Request path`
and later execution under `Worker path` so that the main time boundary remains
legible at book size. The detailed diagram expands those groups and includes
durable storage, lifecycle events, governed deferred tool execution, retry
scheduling, and abandonment.

## Simplified sequence

```mermaid
sequenceDiagram
    actor Reader
    participant Request as Request path
    participant Scheduler as TaskScheduler
    participant Execution as Worker path

    rect rgb(235, 246, 255)
        Note over Reader,Scheduler: Request time
        Reader->>Request: Generate a summary in five minutes
        Request->>Scheduler: Store the scheduled task
        Scheduler-->>Request: Task ID and scheduled time
        Request-->>Reader: Confirm that the task is scheduled
    end

    Note over Reader,Scheduler: Original request ends

    rect rgb(245, 240, 255)
        Note over Scheduler,Execution: Later, when the task is due
        Execution->>Scheduler: Get due tasks
        Scheduler-->>Execution: Stored task
        Execution->>Execution: Execute through the command pipeline
        Execution->>Scheduler: Save completed result
    end
```

## Detailed sequence

```mermaid
sequenceDiagram
    autonumber

    actor Caller
    participant Handler as RequestHandler
    participant Mediator as ConversationMediator
    participant State as ConversationEngine / ExecutingState
    participant Tools as ToolExecutor
    participant Pipeline as Handler pipeline
    participant Schedule as ScheduleTaskCommand
    participant Clock
    participant Scheduler as TaskScheduler
    participant Store as In-memory or SQLite store
    participant Worker
    participant Events as EventPublisher
    participant Registry as TaskExecutorRegistry
    participant Retry as RetryPolicy
    participant Deferred as Deferred command

    rect rgb(235, 246, 255)
        Note over Caller,Store: Request-time admission and persistence
        Caller->>Handler: Submit a request to run work later
        Handler->>Mediator: Run the request lifecycle
        Mediator->>State: Execute the selected schedule_task tool
        State->>Tools: execute_tool(schedule_task)
        Tools->>Tools: Resolve ScheduleTaskCommand
        Tools->>Pipeline: Apply the strict execution policy
        Pipeline->>Schedule: execute(ToolContext)
        Schedule->>Clock: now()
        Clock-->>Schedule: Time-zone-aware current time
        Schedule->>Schedule: Parse schedule and build BackgroundCommand
        Schedule->>Schedule: Preserve correlation and idempotency identities
        Schedule->>Scheduler: schedule(task)
        Scheduler->>Store: Persist task with status scheduled
        Store-->>Scheduler: Task stored
        Scheduler-->>Schedule: Stored task
        Schedule-->>Pipeline: Task ID, scheduled time, and status
        Pipeline-->>Tools: Completed ToolContext
        Tools-->>State: Scheduling result
        State-->>Mediator: Response with scheduling confirmation
        Mediator-->>Handler: Request result
        Handler-->>Caller: Confirm accepted work and return task ID
    end

    Note over Caller,Store: Original request ends

    rect rgb(245, 240, 255)
        Note over Clock,Deferred: Worker-time execution
        Worker->>Clock: now()
        Clock-->>Worker: Current time
        Worker->>Scheduler: next_due_tasks(now)
        Scheduler->>Store: Query scheduled tasks due by now
        Store-->>Scheduler: Due task records
        Scheduler-->>Worker: Due tasks

        loop For each due task
            Worker->>Scheduler: save(status=running)
            Scheduler->>Store: Persist running state
            Worker->>Events: Publish task.started
            Worker->>Registry: execute(task)

            alt Deferred tool command
                Registry->>Tools: execute_tool(name, args, identities)
                Tools->>Pipeline: Apply the command's execution policy
                Pipeline->>Deferred: execute(ToolContext)
                Deferred-->>Pipeline: Result
                Pipeline-->>Tools: Completed ToolContext
                Tools-->>Registry: Result
            else Generic background task
                Registry->>Deferred: Execute the registered generic handler
                Deferred-->>Registry: Result
            end

            alt Execution succeeds
                Registry-->>Worker: Result
                Worker->>Events: Publish task.completed
                Worker->>Scheduler: save(status=completed, result)
                Scheduler->>Store: Persist terminal result
            else Execution raises an exception
                Registry--xWorker: Exception
                Worker->>Events: Publish task.failed
                Worker->>Worker: Record error and increment retries

                alt Retry budget remains
                    Worker->>Retry: next_delay(retries)
                    Retry-->>Worker: Retry delay
                    Worker->>Worker: Set new scheduled time and status scheduled
                    Worker->>Events: Publish task.retried
                    Worker->>Scheduler: save(rescheduled task)
                    Scheduler->>Store: Persist error, retry count, and new time
                else Retry budget is exhausted
                    Worker->>Worker: Set status abandoned
                    Worker->>Events: Publish task.abandoned
                    Worker->>Scheduler: save(abandoned task)
                    Scheduler->>Store: Persist terminal error state
                end
            end
        end
    end
```

## Reading the diagrams

- `Request path` groups `RequestHandler`, `ConversationMediator`,
  `ConversationEngine`, `ToolExecutor`, the strict handler pipeline, and
  `ScheduleTaskCommand`. It is a visual grouping, not an additional runtime
  class.
- `Worker path` groups `Worker`, `TaskExecutorRegistry`, `ToolExecutor`, and the
  governed command pipeline. It is also a visual grouping rather than a new
  runtime class.
- The request returns only after `TaskScheduler` has accepted the durable task.
  The returned task ID is the handle for later inspection.
- `TaskScheduler` owns persistence and eligibility. It does not execute the
  task or decide retry delays.
- `In-memory or SQLite store` represents storage owned by the concrete
  scheduler implementation. It is a visual grouping, not a separate runtime
  service.
- `Worker` owns lifecycle transitions. It stores `running` before execution,
  publishes task events, records the result or error, and persists the next
  state.
- A deferred tool command returns through the owning runtime's `ToolExecutor`,
  so the stored command crosses the same governed handler pipeline as immediate
  tool work. Stable correlation and idempotency identities cross that boundary.
- A retryable failure returns the durable task to `scheduled` with a new
  eligibility time. Exhausting the retry budget moves it to `abandoned`.

## Scope

The compact sequence focuses on the boundary between accepted work and later
execution. It intentionally hides request planning, registry lookup, policy
handlers, events, retry branches, and storage implementation details.

The detailed sequence follows the scheduling and worker responsibilities but
still groups individual policy handlers and event observers. It omits model
generation, response decoration, session persistence, distributed worker
claims, recurring schedules, and exactly-once delivery. Those concerns either
belong to other chapter diagrams or require infrastructure beyond the local
worker described in Chapter 10.

## Related implementation

- [`ScheduleTaskCommand`](../../../metis/commands/schedule.py)
- [`BackgroundCommand`, `TaskScheduler`, and scheduler implementations](../../../metis/scheduling/scheduler.py)
- [`Worker`](../../../metis/scheduling/worker.py)
- [`TaskExecutorRegistry`](../../../metis/scheduling/executors.py)
- [Retry policies](../../../metis/scheduling/retry.py)
- [Clock implementations](../../../metis/scheduling/clock.py)
- [`ToolExecutor`](../../../metis/tools/tool_executor.py)
- [Runtime assembly and deferred tool execution](../../../metis/services/services.py)
- [Provider-free Chapter 10 example](../../../metis/examples/chapter10_background_tasks.py)

## Focused verification

- [`test_schedule_task_command.py`](../../../tests/commands/test_schedule_task_command.py)
- [`test_background_scheduler.py`](../../../tests/scheduling/test_background_scheduler.py)
- [`test_sqlite_scheduler.py`](../../../tests/scheduling/test_sqlite_scheduler.py)
- [`test_scheduler_worker.py`](../../../tests/scheduling/test_scheduler_worker.py)
- [`test_worker_events.py`](../../../tests/scheduling/test_worker_events.py)
- [`test_scheduling_flow.py`](../../../tests/integration/test_scheduling_flow.py)
- [`test_full_workflow.py`](../../../tests/integration/test_full_workflow.py)
- [`test_chapter10_background_tasks.py`](../../../tests/examples/test_chapter10_background_tasks.py)

Run the provider-free example and focused tests from the repository root:

```sh
python -m metis.examples.chapter10_background_tasks --delay-minutes 5
pytest -q \
  tests/commands/test_schedule_task_command.py \
  tests/scheduling/test_background_scheduler.py \
  tests/scheduling/test_sqlite_scheduler.py \
  tests/scheduling/test_scheduler_worker.py \
  tests/scheduling/test_worker_events.py \
  tests/integration/test_scheduling_flow.py \
  tests/examples/test_chapter10_background_tasks.py
```
