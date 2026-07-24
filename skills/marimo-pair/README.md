# marimo-pair (wrapper)

This directory is a **wrapper skill**. It is not the real skill.

## Why this exists

`m-pair` (a symlink to `~/.claude/custom/plugins/marimo-pair/skills/marimo-pair`,
backed by the `marimo-team/marimo-pair` git submodule) holds the actual skill
content. We keep the submodule unmodified so it can track upstream cleanly.

This `marimo-pair` directory is a thin wrapper that preserves the
user-facing invocation name (`/marimo-pair`) while delegating to `m-pair` for
everything. The wrapper also records a local gotcha (the `execute-code.sh`
auth-token handling) that we do not want to push into the upstream submodule.

## Layout

```
~/.claude/skills/
  m-pair -> ../custom/plugins/marimo-pair/skills/marimo-pair   # real skill (submodule)
  marimo-pair/                                                 # this wrapper
    SKILL.md   # delegates to m-pair
    README.md  # this file
```

## To change the real skill

Edit the submodule at `~/.claude/custom/plugins/marimo-pair/` (separate git
repo). Do not edit it through this wrapper.
