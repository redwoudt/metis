# Architecture diagrams

This directory contains detailed diagrams that connect the design-pattern
explanations in *Design Patterns in Practice* to the Mêtis implementation. The
book keeps its diagrams focused on the main architectural idea; the diagrams
here may show the complete runtime flow, optional branches, and implementation
links.

## Diagram index

- [Chapter 2 request lifecycle](chapter-02/request-lifecycle.md) — the detailed
  path from `RequestHandler` through `ConversationMediator` and its runtime
  collaborators.
- [Chapter 18 full workflow](../full_workflow.md) — the end-to-end workflow that
  brings the book's patterns together.

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

