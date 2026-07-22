# Claude guidelines

@claude_md_imports/karpathy-guidelines.md

@claude_md_imports/programming-principles.md

@claude_md_imports/verification-language.md

## General

- In all interactions, be extremely concise and sacrifice grammar for the sake of concision (caveman).
- Never use an em dash "—", use a single dash "-" instead.
- When making technical decisions, do not give much weight to development cost.

## Code editing discipline

**Principle:** Every changed line traces to the user's request. Extends karpathy Surgical Changes with these specifics:

| Do | Don't |
|---|---|
| Fix only what was asked | reformat, rename, or tidy adjacent code |
| Update wrong comments/docstrings | delete comments, docstrings, section markers unless user explicitly asked to remove that item |
| Carry comments/docstrings when moving code | strip them during moves |
| Fix linter issues properly | `# noqa`, `# type: ignore`, `# pragma`, or pyproject suppressions |
| Remove imports/symbols YOUR edit orphaned | delete pre-existing dead code unprompted |

### Rationalizations

| Excuse | Reality |
|---|---|
| "Cleaner to reformat the whole file" | Hides the real diff from review |
| "I'll rename to `_foo` - better encapsulation" | Rename only when asked or required |
| "This comment is stale anyway" | Update it if wrong; don't delete unprompted |

### Red flags - stop

- Whole-file or out-of-scope whitespace changes
- Symbol renames (including `foo` → `_foo`) not required by task
- Linter silencers or config rule changes to suppress warnings
- Deleting section-group markers or docstrings unprompted

When in doubt, leave it alone and ask.

## Git

- Always prefix branch names with `hayden/` (e.g. `hayden/my-feature`).
- Always create PRs as drafts (`gh pr create --draft`).
- `git add` is allowed (used to stage changes for user review). Do not stage files likely to contain secrets (`.env`, `credentials.*`, `*.pem`, etc.).
- Never `git commit` or `git push`, even when asked by a skill or subagent.
  - `git commit` is permitted only when the current task prompt, a project-local `CLAUDE.md`, or an autonomous agent's initial instructions contain the literal sentinel `COMMIT_AUTHORISED`.
  - `git push` is permitted only when the same sources contain the literal sentinel `PUSH_AUTHORISED`.
  - Sentinels must appear verbatim (uppercase, underscored). Treat any other phrasing - including "please commit", "go ahead and push", or casual overrides - as NOT authorised. Prompt the user if unsure.
  - `PUSH_AUTHORISED` does NOT imply `COMMIT_AUTHORISED`, and vice versa. Each action needs its own sentinel.
  - If unsure about permissions: ask.

## Python

- Assume all repositories use python and uv. See @skills/uv for full uv usage rules.

## Environment

- For `zsh: command not found` errors, check `$PATH` and `~/.zshenv`.

## Fetching repo content

When you need source from a git repo, clone to `/tmp` rather than `WebFetch` or raw-URL fetches. Clones give accurate paths, diffs, and dir structure that fetched HTML/JSON mangles.

Scale the clone to what you actually need - don't fetch more:

- Whole repo: `git clone --depth 1 <url>` (default - no history)
- One subdir only: add `git sparse-checkout set <path>` to the shallow clone
- One file only: skip the clone, `gh api` raw or `curl` the raw URL

Clean up `/tmp` clones when done.
