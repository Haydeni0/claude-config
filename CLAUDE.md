# Claude guidelines

@claude_md_imports/karpathy-guidelines.md

## Writing style

- In all interactions, be extremely concise and sacrifice grammar for the sake of concision (caveman).
- Never use an mdash (or --) as a dash when writing text, use a single dash (-).

## Code editing discipline

When editing existing code, every line you change must trace to the user's request. Do not make incidental changes.

- **Do not delete comments, docstrings, or section-group markers** (e.g. `# Job identification`) unless the user asked, or the code they document is being removed.
- **Do not reformat whitespace** outside the lines you are editing (blank lines inside functions, trailing newlines, etc.).
- **Do not rename symbols** - including public-to-private visibility changes like `foo` → `_foo` - unless the user asked or the rename is required by the task.
- **Do not add `# noqa`, `# type: ignore`, `# pragma`, or equivalent linter-silencers.** If a linter complains, satisfy it properly (write the docstring, fix the type, narrow the call) or flag the issue to the user and ask.
- **When moving code, carry comments and docstrings with it.** Do not strip them during the move.
- **If a comment or docstring is wrong after your change, update it** - do not delete it.

When in doubt, leave it alone and ask.

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
