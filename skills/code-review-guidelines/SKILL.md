---
name: code-review-guidelines
description: Review criteria and output format for code reviews. Covers correctness, security, performance, readability, breaking changes, dependencies, and test coverage.
user-invocable: false
---

## Review criteria

Evaluate against these criteria (skip any that don't apply):

- **Correctness**: Bugs, edge cases, off-by-one errors, race conditions
- **Security**: Injection, auth gaps, secrets, input validation
- **Performance**: Unnecessary allocations, O(n²) where O(n) is possible, missing indexes, unnecessary I/O in hot paths, missing caching opportunities (in non-negligible cases)
- **Readability**: Naming, structure, unnecessary complexity, deep nesting, unclear control flow, functions that are too long to hold in your head
- **Maintainability**: Separation of concerns, tight coupling, scattered cohesion, duplicated logic, unclear module boundaries, hardcoded assumptions, over/under-abstraction
- **Breaking changes**: API surface, backward compatibility, config changes
- **Dependencies**: New dependencies justified and secure
- **Missing coverage**: Untested paths that should have tests (note them, don't write them)

## Output format

```
## Summary
One-line description of what this change does.

## Findings

### Critical
- [file:line] Description

### Major
- [file:line] Description

### Minor / Nits
- [file:line] Description

## Questions
Things that are unclear or need author clarification.

## Verdict
Approve / Request Changes / Comment — with brief justification.
```

## Guidelines

- Keep findings concise and actionable. Reference specific lines.
- Do not suggest stylistic changes unless they hurt readability.
- Do not flag pre-existing issues unrelated to the current changes.
