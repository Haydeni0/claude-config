# claude-config

Backup of `~/.claude` config — the single source of truth for [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [opencode](https://opencode.ai), and [pi](https://pi.dev).

## What's tracked

- `CLAUDE.md` — global memory/instructions
- `claude_md_imports/` — files imported into `CLAUDE.md` via `@` syntax
- `settings.json` — permissions and plugin config
- `skills/` — custom skills (some symlink into `custom/plugins/caveman`)
- `agents/` — custom subagents (`code-reviewer`, `meta-reviewer`)
- `commands/` — custom slash commands
- `custom/` — hooks and plugins (includes [caveman](https://github.com/JuliusBrussee/caveman) submodule)
- `hooks/` + `RTK.md` — RTK token-rewrite hook
- `statusline-command.sh` — CLI statusline
- `opencode/` — base opencode config (`opencode.json`, `tui.json`), synced by settings-sync
- `settings-sync/` — syncs this config into [opencode](https://opencode.ai) and [pi](https://pi.dev); see [settings-sync/README.md](settings-sync/README.md)
- `pi/` — base pi config (pointer template + pinned `packages[]`), wired by `sync`; see [pi/README.md](pi/README.md)
- `sync.sh` — one-command machine setup: runs settings-sync + installs the machine-local tools the repo declares ([evo](https://github.com/evo-hq/evo) for claude-code/opencode, pi packages incl. [pi-web-access](https://github.com/nicobailon/pi-web-access))

## Typical workflows

> Personal notes. One conversation unless context stale or switching repos.
>
> Single living spec; after Interfaces and Tests grills: `Fold our decisions into the spec. Also, review the spec for consistency after.`

### Feature pipeline

- **Understand** — `Help me plan <feature>. <why> <starter idea> <existing integration surface in repo> /grill-me` — exit: scope, non-goals, key decisions agreed
- **Spec** — `Write a spec from our agreed design. /superpowers:brainstorming` — exit: spec file exists and reviewed
- **Interfaces** — `Help me brainstorm interfaces/classes for this spec. /grill-me` — exit: protocols, classes, module layout agreed — then: spec merge
- **Tests** — `Help me plan tests for this spec before we implement. /grill-me /pytest-guidelines` — exit: public API test strategy agreed — then: spec merge
- **Implement** — `Implement per spec. /tdd` — exit: `tdd_scaffolding/` deleted; behavioral tests pass per `pytest-guidelines`

## Install (new machine)

`~/.claude` is the single source of truth — Claude Code, opencode, and pi all read from it.
Get the repo, then wire up whichever tools you use.

### 1. Get the repo

```bash
# If ~/.claude doesn't exist yet
git clone --recurse-submodules git@github-haydeni0:Haydeni0/claude-config.git ~/.claude

# If ~/.claude already exists (Claude Code was already run)
cd ~/.claude
git init
git remote add origin git@github-haydeni0:Haydeni0/claude-config.git
git fetch origin
git checkout -f main
git submodule update --init --recursive
```

### 2. Wire up your tools

**Claude Code** reads `~/.claude` directly — nothing to run.

**opencode** and **pi** are both synced by `settings-sync`, and the machine-local tools the repo declares (evo, pi packages) are installed by `sync.sh`. Both need [uv](https://docs.astral.sh/uv/).

```bash
# install opencode: https://opencode.ai  •  install pi: https://pi.dev  (e.g. curl -fsSL https://pi.dev/install.sh | sh)
bash ~/.claude/sync.sh                                    # one command: settings-sync + install evo + pi packages
uv run --directory ~/.claude/settings-sync sync opencode # granular: opencode config only (no installs)
uv run --directory ~/.claude/settings-sync sync pi       # granular: pi config only (no installs)
uv run --directory ~/.claude/settings-sync sync --check  # drift check (read-only)
# tip: alias ssync='uv run --directory ~/.claude/settings-sync sync' for brevity
```

- **sync.sh** — runs settings-sync, then materializes machine-local installs: `pi install` for each entry in `pi/settings.json#packages[]` (evo + pi-subagents + pi-web-access), and `evo install` for claude-code/opencode (skipped if that host isn't on PATH). Idempotent; re-run after `git pull` or any `~/.claude` edit.
- **opencode** — derives config into `~/.config/opencode`; re-run `sync.sh` (or `sync`) after every `~/.claude` edit.
- **pi** — writes pointers + inlined context + `packages[]` into `~/.pi/agent`; skills/commands are read directly (just `/reload` in pi after edits), only the context file is derived.

See [settings-sync/README.md](settings-sync/README.md) and [pi/README.md](pi/README.md).

## Update

```bash
cd ~/.claude
git add -A
git commit -m "update"
git push
```

To pull in a newer caveman release:

```bash
cd ~/.claude/custom/plugins/caveman && git pull
cd ~/.claude && git add custom/plugins/caveman && git commit -m "bump caveman" && git push
```
