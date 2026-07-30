# marimo gotchas

Hard-won marimo quirks. One pattern per heading. Keep entries terse: what doesn't
work, what does, one line each. No preamble, no examples beyond the pattern itself.
When adding: distill to the essential insight - if a future agent can't act on it in
3 lines, it's too verbose. Use `#` headings, bullets for the do/don't pairs.

# Display gotcha (marimo 0.23)

Cells whose output is in an `if/else` branch won't show in the UI unless assigned to a **public** name.

- `_ = mo.hstack(...)` - does NOT render. `_` prefix = private, suppressed.
- bare `mo.hstack(...)` at end of a branch - does NOT render. No public def for marimo to display.
- `name = mo.hstack(...)` then `name` on the last line - DOES render.

marimo-check's `_ =` suggestion for "branch expression won't display" is wrong for runtime display - it silences the output. Use a public name + final-line reference instead.

# Reset UI elements (marimo 0.23)

To reset sliders/widgets to defaults, **re-run the cell that creates them**. The cell recreates the widgets with their `value=` defaults.

- Put the reset button in a **separate cell** (you can't read `button.value` in the cell that creates it).
- The slider cell references `reset_button.value` so it re-runs on click, recreating all widgets fresh.
- `on_change` callback + `element._update(value)` does NOT push to the frontend UI - it sets internal state only.
- `cm.get_context().set_ui_value()` can't be called inside a notebook cell ("NotebookDocument not available"). It only works from the scratchpad/external API.

