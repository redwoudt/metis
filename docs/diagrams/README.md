# Architecture diagrams

This directory contains detailed diagrams that connect the design-pattern
explanations in *Design Patterns in Practice* to the Mêtis implementation. The
book keeps its diagrams focused on the main architectural idea; the diagrams
here may show the complete runtime flow, optional branches, and implementation
links.

## Diagram index

- [Chapter 1 request journey](chapter-01/request-journey.md)
  describes the compact request path used in the opening chapter, with runtime
  collaborators and evidence services grouped for readability.
- [Chapter 2 request lifecycle](chapter-02/request-lifecycle.md)
  describes the detailed path from `RequestHandler` through
  `ConversationMediator` and its runtime collaborators.
- [Chapter 5 prompt DSL runtime](chapter-05/prompt-dsl-runtime.md)
  contains the compact book sequence and detailed component-level path through
  lexing, parsing, expression evaluation, semantic validation, and prompt
  construction.
- [Chapter 6 model-management runtime](chapter-06/model-management-runtime.md)
  shows first-use client creation, same-key reuse, and governed generation
  through `ModelFactory`, the reuse cache, and `ModelProxy`.
- [Chapter 8 governed tool execution](chapter-08/tool-execution-lifecycle.md)
  expands the printed sequence into allow-listed lookup, policy selection,
  handler-chain outcomes, lifecycle events, and result recording.
- [Chapter 9 adaptive response runtime](chapter-09/adaptive-response-runtime.md)
  contains the compact book sequence and detailed component-level path through
  Strategy selection, model generation, and deterministic Decorator
  composition.
- [Chapter 10 background-task lifecycle](chapter-10/background-task-lifecycle.md)
  contains the compact book sequence and detailed component-level path through
  task creation, persistence, later worker execution, governed deferred tool
  execution, lifecycle events, retries, and abandonment.
- [Chapter 12 mediated request lifecycle](chapter-12/mediator-request-lifecycle.md)
  expands the compact success and policy-denial sequence into the complete
  mediated lifecycle, including events, request planning, execution,
  persistence, and failure propagation.
- [Chapter 14 memory checkpoint lifecycle](chapter-14/memory-checkpoint-lifecycle.md)
  contains the compact book sequence and a detailed save-and-restore flow,
  including artifact pinning, persistence, release, and missing-artifact
  failure behavior.
- [Chapter 15 null publisher lifecycle](chapter-15/null-publisher-lifecycle.md)
  expands the compact model-request sequence into publisher normalization,
  real and null delivery behavior, and the success and failure paths.
- [Chapter 18 full workflow](../full_workflow.md)
  shows the end-to-end workflow that brings the book's patterns together.

## Conventions

- Use a zero-padded directory name such as `chapter-02`.
- Use lowercase, kebab-case filenames that describe the behavior shown.
- Keep the editable Mermaid source inside the Markdown file so that GitHub can
  render it and the repository has one source of truth.
- State what the diagram includes and intentionally omits.
- Link to the implementation and the focused tests that support the diagram.
- Use the book's architecture vocabulary consistently: Facade for the public
  request entry, Mediator for lifecycle ordering, and Services for assembly.
- Update a diagram in the same change as any code that invalidates it.

## Referencing diagrams

Repository documentation should use relative links. Published material should
use a GitHub permalink pinned to the commit or release that the text describes,
not a link to a moving branch such as `main`.
