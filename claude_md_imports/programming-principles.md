# Programming Principles

What good code looks like. Always-loaded, so kept to universal principles only.
Apply when writing, reviewing or editing code.

- Scope: behavioral/process rules live in karpathy-guidelines. This file is about the code itself.
- A principle belongs here only if it is (1) universal - true regardless of feature/design, (2) about the code not the process, (3) not already covered elsewhere. Design-dependent preferences ("use Protocols here") do NOT belong - they are conditional.

## General

- **Name by what a thing is or does, not what it's used for.** Usage-based names rot the moment the same code serves a second caller.

  ```python
  # bad
  user_list_for_dropdown
  # good
  active_users
  ```

- **Comment the *why*, never the *what*.** If the "what" needs a comment, rename or restructure instead.

  ```python
  # bad
  i += 1  # increment i
  # good
  i += 1  # skip the header row; the export always has one
  ```

- **No lineage or incident history in docstrings or comments.** "Moved from X", "Rehomed from Y", "Previously in Z" describe git history, not behavior. "See incident #123", "we used to do X but crashed so switched to Y", "fixed bug N", past decision rationale (KV-pool math, crash root-causes, perf-incident refs) describe *why a past decision was made* - equally unreadable by a new reader, and they rot fast (the crash is gone, the flag is renamed, the number drifts). Both go in the commit message or PR body, not the code. A comment should explain a *current* constraint a reader must respect to work with the code safely, not how the code got here. Exception: a live deprecation notice ("old import still works but is deprecated") is actionable - remove it once the old path is gone.

- **Flatten with guard clauses; don't nest the happy path.** Early return/raise on preconditions, then the main logic sits unindented.

- **A boolean/flag parameter means the function does two things - prefer named alternatives.** Two functions, or an enum, over a bare boolean - the call site `render(True)` tells the reader nothing.

  ```python
  # bad
  render(is_admin)
  # good
  render_admin() / render_user()   # or render(role=Role.ADMIN)
  ```

- **Don't add silent fallbacks or default values on unexpected failure.** Let it fail loudly with context, unless a fallback was explicitly asked for. Masked failures produce wrong output instead of a visible crash.

- **Don't duplicate logic that already exists, and use the project's wrapper over the raw library.** Duplicated validators/clients/utils diverge over time; bypassing a wrapper sidesteps its auth, logging, and error handling.

- **Keep functions pure by default; push side effects to the boundary.** A function that mixes computation with I/O or state mutation is harder to test and reason about. Separate the two unless the side effect is the function's whole purpose.

- **Error messages must carry actionable context** - what operation failed, the relevant inputs, and enough state to reproduce.

  ```python
  # bad
  raise ValueError("error")
  # good
  raise ValueError(f"API call failed: status={resp.status_code} params={params} body={resp.text[:500]}")
  ```

- **Give every meaningful literal a named constant whose name encodes the reason**, not just the value. `MINIMUM_LEGAL_AGE`, not a bare `18`.

- **Keep all statements in a function at one level of abstraction.** Don't mix high-level intent (`process_payment()`) with low-level mechanics (`cart.items[i].price * 0.9`) in the same body; extract the detail.

- **Don't extract a shared abstraction until the third occurrence.** Two instances rarely reveal the right generalisation; premature extraction locks in the wrong shape.

- **Prefer composition over inheritance, and depend on behavior not concrete type.** Inheritance couples a subclass to its parent's internals and forces a single hierarchy; composition keeps pieces swappable. Where a seam is needed, type against an interface (e.g. a `Protocol`) so callers depend on what a thing does, not what it is. Don't add the interface until a second implementation makes the seam real.

  ```python
  # bad - subclass to reuse, locks the hierarchy
  class CsvReport(Database): ...
  # good - compose the dependency
  class CsvReport:
      def __init__(self, store: SupportsRead): ...
  ```

## Python

- **Use `X | None` and builtin generics, not `Optional` / `typing.List`.** (3.10+)

  ```python
  # bad
  def f(x: Optional[str]) -> List[int]: ...
  # good
  def f(x: str | None) -> list[int]: ...
  ```

- **Use `pathlib.Path` over `os.path`** for all filesystem work - composable with `/`, cross-platform, covers what `os`/`os.path`/`shutil` did separately.

- **Use a structured model (dataclass / pydantic) over `dict` or `Any` for data with a known shape.** `dict[str, Any]` defeats type checking and lets schema violations slip to runtime.

- **Keep types sound - don't suppress.** Avoid `# type: ignore` and `Any`; fix the type or signature instead. If truly unavoidable, scope the ignore to a code (`# type: ignore[code]`) and say why. Prefer narrowing (`isinstance`, overloads, `TypeGuard`) over widening to `Any`.

- **Default new dataclasses to `@dataclass(slots=True)`; add `frozen=True` for value objects** (immutable, hashable, usable as a dict key).

- **Use `StrEnum` (3.11+) for string-valued enums.** Members are strings directly - no `.value` unwrapping at every call site.

- **Re-raise with explicit chaining.** `raise NewError(...) from exc`; use `from None` only to deliberately suppress the chain. Attach context with `exc.add_note(...)` (3.11+) rather than wrapping in a new exception just for a message.

- **Prefer EAFP (try/except) for operations that genuinely fail at runtime** (I/O, lookups) - a check-then-act has a TOCTOU race. But don't use exceptions to branch on *expected* business logic; that's control flow, use a conditional.

- **Don't use f-strings in `logging` calls** - they evaluate eagerly even when the log level is suppressed; pass lazy `%` args. (`f"{x=}"` is handy for debug output, though.)

  ```python
  # bad
  logging.debug(f"processing {expensive()}")
  # good
  logging.debug("processing %s", expensive())
  ```

- **Use a generator expression, not a list comprehension, when the result is iterated once** or passed to `sum`/`any`/`all`/`max`. O(1) peak memory instead of building a throwaway list - but only safe for a single pass; assign to a list if you iterate more than once.

- **Use absolute imports, not relative imports.** Exception: `__init__.py` re-exports (`from .module import Thing`) are fine.
