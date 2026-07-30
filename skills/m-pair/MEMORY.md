# Display gotcha (marimo 0.23)

Cells whose output is in an `if/else` branch won't show in the UI unless assigned to a **public** name.

- `_ = mo.hstack(...)` - does NOT render. `_` prefix = private, suppressed.
- bare `mo.hstack(...)` at end of a branch - does NOT render. No public def for marimo to display.
- `name = mo.hstack(...)` then `name` on the last line - DOES render.

marimo-check's `_ =` suggestion for "branch expression won't display" is wrong for runtime display - it silences the output. Use a public name + final-line reference instead.
