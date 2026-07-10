# settings-sync

Syncs `~/.claude` config into both [opencode](https://opencode.ai) (`~/.config/opencode`) and [pi](https://pi.dev) (`~/.pi/agent`). `~/.claude` stays the single source of truth; the target dirs are fully derived and regenerated on each run.

`~/.claude` is your git repo — `git pull` on any machine, then `sync`. Skills and commands are read directly by both tools (no duplication); only the things each tool can't read natively are derived.

## What it syncs

### opencode

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

Hooks (`hooks/`) are not bridged — opencode's plugin hook model differs. Recreate as an opencode plugin if needed.

### pi

| Source in `~/.claude` | Target in `~/.pi/agent` | Mechanism |
|---|---|---|
| `pi/settings.json` (pointer template) | `settings.json` | **wholesale copy** (template is SOT; pi's own keys are disposable) |
| `CLAUDE.md` + `@` imports | `CLAUDE.md` | inlined (`@path` imports expanded, `@skills/<n>` rewritten) — pi can't expand `@` imports |
| `skills/` | (native) | pi reads `~/.claude/skills` directly (via pointers); tool validates only |
| `commands/` | (native) | pi reads `~/.claude/commands` directly (via pointers) |

pi's `settings.json` is **wholesale-copied** (no merge, no preserved machine keys): `lastChangelogVersion` and other pi-owned state self-heal on next pi run. Per-machine model/auth/provider choices belong in `auth.json`/`models.json`/env, not `settings.json`. See [`pi/README.md`](../pi/README.md).

## Usage

```bash
# In the examples below, `sync` is the invocation from Run above, i.e.
# `uv run --directory ~/.claude/settings-sync sync` (or your `ssync` alias).

# sync everything (opencode + pi); refuse on conflict, exit 1 if any conflict
sync
sync all                       # explicit

# per tool
sync opencode                  # all opencode steps
sync pi                        # pointers + inlined context
sync opencode config           # one step (config|tui|agents-md|agents|commands|plugins|skills)
sync pi config                 # one step (config|context|skills)

# flags (before the group name)
sync --dry-run                 # preview, write nothing
sync --check                   # exit nonzero on drift, write nothing
sync --force                   # clobber diverging derived files
sync --verbose                 # show diffs for changed text artifacts
sync --pi-dir /tmp/glm-pi pi   # target a different pi agent dir
```

Global options (`--force`, `--dry-run`, `--check`, `--verbose`, `--claude-dir`, `--opencode-dir`, `--pi-dir`) go before the subcommand. Override paths for testing or alternate harnesses.

## Run

Stateless — no install step, just run it from the repo each time (needs [uv](https://docs.astral.sh/uv/)):

```bash
uv run --directory ~/.claude/settings-sync sync          # sync everything (opencode + pi)
uv run --directory ~/.claude/settings-sync sync opencode # granular
uv run --directory ~/.claude/settings-sync sync pi       # granular
# tip: alias ssync='uv run --directory ~/.claude/settings-sync sync' for brevity
```

No persistent install, no shim on PATH — `git pull` and you're on the latest version. (If you prefer a global command, `uv tool install ~/.claude/settings-sync` puts `sync` on PATH, but you must reinstall to update.)

## Conflicts and safety

- By default the tool **refuses to delete or overwrite** anything it didn't create. A conflicting real file/dir at a managed path is skipped with a warning.
- `--force` removes/replaces conflicting managed paths, reconciles orphaned agent files (target `.md` not in source), and retargets wrong symlinks.
- No files are deleted without `--force`.
- **Exception — pi config:** `settings.json` is always overwritten (wholesale copy; the template is SOT). `--force` is not needed for it.
- opencode manages only: `opencode.json`, `tui.json`, `AGENTS.md`, `agents/`, `commands`, `plugins/superpowers.js`. Everything else in `~/.config/opencode` is left untouched.
- pi manages only: `settings.json`, `CLAUDE.md`. Everything else in `~/.pi/agent` (auth, sessions, bin, models.json) is left untouched.

## Agent frontmatter transform (opencode only)

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
- **opencode-only keys** (`question`, `lsp`, `websearch`, `external_directory`, `doom_loop`) are left unset — they have no Claude Code equivalent, so no restriction is invented.
- **Skills**: `skills: [a, b]` -> `skill: {"*": "deny", "a": "allow", "b": "allow"}`.
- **Unknown tools**: warned, skipped.
- **`mode`** defaults to `subagent` (Claude Code custom agents are subagents).

## Run after editing `~/.claude`

After changing anything in `~/.claude`, re-run `sync` (or the relevant group). It is idempotent — unchanged artifacts report `unchanged`, changed ones update.

- **Skills/commands** are read directly by both tools — editing them needs only a `/reload` in pi (opencode picks them up live via symlink), no re-sync required.
- **Derived files** (opencode's `AGENTS.md`/`agents/`/`opencode.json`, pi's `settings.json`/`CLAUDE.md`) update on next `sync` run. So: edit CLAUDE.md or its `@` imports → `sync` to refresh both `AGENTS.md` (opencode) and `CLAUDE.md` (pi).
