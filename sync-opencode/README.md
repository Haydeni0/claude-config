# sync-opencode

Bridges `~/.claude` config into `~/.config/opencode` so both Claude Code and opencode read from a single source of truth. `~/.claude` stays the source; `~/.config/opencode` is fully derived and regenerated on each run.

## What it syncs

| Source in `~/.claude` | Target in `~/.config/opencode` | Mechanism |
|---|---|---|
| `opencode/opencode.json` (base config) | `opencode.json` | passthrough, adds `$schema` |
| `opencode/tui.json` (TUI config) | `tui.json` | passthrough, adds `$schema` |
| `opencode/rules.md` (opencode-only rules) | appended to `AGENTS.md` | safety rules appended after CLAUDE.md content |
| `CLAUDE.md` + `@` imports | `AGENTS.md` | `@path` imports inlined recursively, `@skills/<n>` rewritten to `the \`<n>\` skill` |
| `agents/*.md` | `agents/*.md` | frontmatter transform (see below) |
| `commands/` | `commands` | relative symlink |
| `plugins/cache/.../superpowers/<v>/.opencode/plugins/superpowers.js` | `plugins/superpowers.js` | relative symlink, highest semver resolved |
| `skills/` | (native) | opencode reads `~/.claude/skills` directly; tool validates only |

Hooks (`hooks/`) are not bridged - opencode's plugin hook model differs. Recreate as an opencode plugin if needed.

## Agent frontmatter transform

Claude Code `tools`/`disallowedTools`/`skills` map to opencode `permission`:

| Claude Code | opencode permission |
|---|---|
| `Read` | `read` |
| `Write`, `Edit`, `apply_patch` | `edit` |
| `Glob`, `Grep` | `glob`, `grep` |
| `Bash` | `bash` |
| `Agent`, `Task` | `task` |
| `List` | `list` |
| `TodoWrite` | `todowrite` |
| `Skill` | `skill` |
| `WebFetch` | `webfetch` |

- **Deny-by-default**: tools not listed in `tools` are `deny` (only for keys with a Claude Code equivalent).
- **opencode-only keys** (`question`, `lsp`, `websearch`, `external_directory`, `doom_loop`) are left unset - they have no Claude Code equivalent, so no restriction is invented.
- **Skills**: `skills: [a, b]` -> `skill: {"*": "deny", "a": "allow", "b": "allow"}`.
- **Unknown tools**: warned, skipped.
- **`mode`** defaults to `subagent` (Claude Code custom agents are subagents).

## Usage

```bash
# sync everything (refuse on conflict, exit 1 if any conflict)
uv run sync-opencode

# preview without writing
uv run sync-opencode --dry-run

# exit nonzero if drift detected (writes nothing)
uv run sync-opencode --check

# clobber conflicting managed paths
uv run sync-opencode --force

# show diffs for changed text artifacts
uv run sync-opencode --verbose
```

Run an individual step: `config`, `tui`, `agents-md`, `agents`, `commands`, `plugins`, `skills`.

```bash
uv run sync-opencode agents          # only transform agents
uv run sync-opencode config          # only write opencode.json
uv run sync-opencode skills          # validate skills, warn only
```

Global options (`--force`, `--dry-run`, `--check`, `--verbose`) apply to the default run and each subcommand. Override paths with `--claude-dir` and `--opencode-dir` (useful for testing).

## Install as a command

```bash
uv tool install ~/.claude/sync-opencode
sync-opencode   # on PATH
```

## Conflicts and safety

- By default the tool **refuses to delete or overwrite** anything it didn't create. A conflicting real file/dir at a managed path is skipped with a warning.
- `--force` removes/replaces conflicting managed paths, reconciles orphaned agent files (target `.md` not in source), and retargets wrong symlinks.
- No files are deleted without `--force`.
- The tool manages only: `opencode.json`, `tui.json`, `AGENTS.md`, `agents/`, `commands`, `plugins/superpowers.js`. Everything else in `~/.config/opencode` (e.g. `package.json`, cache) is left untouched.

## Run after editing `~/.claude`

After changing anything in `~/.claude`, re-run `sync-opencode`. It is idempotent - unchanged artifacts report `unchanged`, changed ones update. Symlinks stay live (editing `~/.claude/commands/foo.md` is immediately visible in opencode); generated copies (agents, AGENTS.md, opencode.json) update on next run.
