# opencode-resume

Resume an opencode conversation inside the current Claude Code session. Reads an opencode session from its SQLite DB, converts it into a markdown transcript, and ingests it as context so the conversation continues in Claude Code.

Companion to [settings-sync](../settings-sync), which bridges *config* (`CLAUDE.md`, agents, skills) into opencode and pi. This tool bridges *conversations*.

## How it works

opencode stores sessions in SQLite (`~/.local/share/opencode/opencode.db`, tables `session` / `message` / `part`). Claude Code has no native way to resume an opencode session, so this converter:

1. Resolves a session (exact id, title substring, or interactive numbered list).
2. Reads its messages and parts in time order.
3. Emits a markdown transcript (`**User:**` / `**Assistant:**` / tool blockquotes) with a metadata header.
4. The `/resume-opencode` slash command runs the converter and ingests the transcript as context in the current Claude session.

No JSONL authoring, no new session file - the transcript becomes the current session's context directly.

## What's kept

- User messages and assistant text replies, in turn order.
- Tool calls: tool name + input, plus output (size-thresholded: `<2KB` kept verbatim, `>=2KB` truncated to 500 chars).
- Reasoning parts and step-start/step-finish markers are dropped.

Only top-level (main thread) sessions are offered; subagent sessions are excluded.

## Usage

Via the slash command (see `../commands/resume-opencode.md`):

```
/resume-opencode                  # list recent sessions, pick by number
/resume-opencode <id>             # exact session id
/resume-opencode <title-substring> # match most recent session by title
```

Or run the converter directly:

```bash
cd ~/.claude/opencode-resume
uv run python -m opencode_resume.cli slurm            # full transcript
uv run python -m opencode_resume.cli slurm --preview   # truncated preview
uv run python -m opencode_resume.cli                  # interactive list
uv run python -m opencode_resume.cli --db /path/to/opencode.db   # custom DB
```

## Development

Stdlib only (sqlite3, json, argparse). Tests use a hermetic synthetic opencode DB (built in `tests/conftest.py`) - never touches the real DB.

```bash
uv run pytest          # 20 keeper tests
```
