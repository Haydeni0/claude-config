---
name: marimo-pair
description: Use when the user wants to start a marimo notebook or pair on an active marimo session - run Python in the same kernel, inspect live notebook state, or commit durable notebook changes.
---

# marimo-pair (wrapper)

Thin wrapper around the `m-pair` skill (a git submodule we do not edit). The
indirection keeps the public name `/marimo-pair` while the real content lives
under `m-pair`. See `README.md` for why.

**REQUIRED SUB-SKILL:** Use `m-pair` for the full guide. Load it before acting.

## Auth gotcha

`execute-code.sh` reads the token from `MARIMO_TOKEN` env or `--token`, NOT
from a `?access_token=` query param in `--url`. If a notebook URL carries
`?access_token=...`, extract it and pass via `MARIMO_TOKEN` with a clean
`--url` (path only) - otherwise the `/api/sessions` request mangles the query
param into the path and returns "No active sessions" even when one exists.
