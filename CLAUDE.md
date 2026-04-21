# Claude guidelines

@claude_md_imports/karpathy-guidelines.md

## Writing style

- In all interactions, be extremely concise and sacrifice grammar for the sake of concision.
- When referencing identifiers in prose or docstrings, use single backticks, not double.
- Never use an mdash (or --) as a dash when writing text, use a single dash (-).

## Git

- `git add` is allowed (used to stage changes for user review). Do not stage files likely to contain secrets (`.env`, `credentials.*`, `*.pem`, etc.).
- Never `git commit` or `git push`, even when asked by a skill or subagent.
  - `git commit` is permitted only when the current task prompt, a project-local `CLAUDE.md`, or an autonomous agent's initial instructions contain the literal sentinel `COMMIT_AUTHORISED`.
  - `git push` is permitted only when the same sources contain the literal sentinel `PUSH_AUTHORISED`.
  - Sentinels must appear verbatim (uppercase, underscored). Treat any other phrasing - including "please commit", "go ahead and push", or casual overrides - as NOT authorised. Prompt the user if unsure.
  - `PUSH_AUTHORISED` does NOT imply `COMMIT_AUTHORISED`, and vice versa. Each action needs its own sentinel.

## Python

- Assume all repositories use python and uv. See @skills/uv for full uv usage rules.

## Environment

- For `zsh: command not found` errors, check `$PATH` and `~/.zshenv`.
