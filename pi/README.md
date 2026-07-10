# pi config (shared, portable)

This directory makes `~/.claude` the **single source of truth** for [pi](https://pi.dev)
resources too. Your skills and commands are already shared with Claude Code; pi reads
them directly via pointers — no duplication, no per-resource symlinks.

Sync is handled by [`settings-sync`](../settings-sync/README.md) (one tool syncs both opencode
and pi): `sync pi` writes the pointer template into `~/.pi/agent/settings.json`
and an inlined `CLAUDE.md` into `~/.pi/agent/CLAUDE.md`.

## Architecture

```
~/.claude/                         <-- git repo (source of truth). git pull on any machine.
├── skills/            <name>/SKILL.md      shared: Claude Code + pi (recursive)
├── commands/          <name>.md            shared: Claude Code commands = pi prompt templates
├── CLAUDE.md                     global context (inlined into pi's CLAUDE.md by settings-sync)
├── claude_md_imports/            @-imports expanded during inlining (pi can't expand them)
├── pi/                                     pi-only resources (Claude ignores these)
│   ├── extensions/    *.ts                 pi extensions
│   ├── themes/        *.json               pi themes
│   ├── settings.json                       pointer template (source of truth for locations)
│   └── README.md                          this file
└── settings-sync/                  the sync tool (opencode + pi)

~/.pi/agent/                       <-- machine-local (NOT in the repo)
├── settings.json                   wholesale copy of pi/settings.json (pointers only)
├── keybindings.json                wholesale copy of pi/keybindings.json (optional)
├── CLAUDE.md                       generated: inlined CLAUDE.md (@imports expanded)
├── auth.json                       credentials (per machine)
├── sessions/                       session history (per machine)
└── bin/rg                          bundled binary (per machine)
```

The pointer template (`pi/settings.json`) is the single source of truth for which dirs pi
reads:
```json
{
  "skills":     ["~/.claude/skills"],
  "prompts":    ["~/.claude/commands"],
  "extensions": ["~/.claude/pi/extensions"],
  "themes":     ["~/.claude/pi/themes"]
}
```
Paths use `~`, so they're identical on every machine. `sync pi config` **wholesale-copies**
this file to `~/.pi/agent/settings.json` — no merge, no preserved machine keys. pi's own state
(e.g. `lastChangelogVersion`, which pi writes after showing a changelog) is disposable: a sync
resets it, pi re-shows the changelog once, then rewrites it. Per-machine model/auth/provider
choices belong in `auth.json`/`models.json`/env, not in `settings.json`.

`sync pi context` inlines `~/.claude/CLAUDE.md` into `~/.pi/agent/CLAUDE.md`: it expands
`@claude_md_imports/*` recursively and rewrites `@skills/<n>` to ``the `<n>` skill`` (pi can't
expand `@` imports itself). This runs by default with `sync pi`; pass `--no-context` is
not needed — opt out via `sync pi config` (context only with `sync pi context`).

## Set up a new machine

```bash
# 1. install pi (no npm/node needed)
curl -fsSL https://pi.dev/install.sh | sh
# fallback if you prefer npm:
#   npm install -g --ignore-scripts @earendil-works/pi-coding-agent

# 2. get your config repo at ~/.claude (clone once, or refresh)
git clone git@github-haydeni0:Haydeni0/claude-config.git ~/.claude   # first time
git -C ~/.claude pull                                               # existing machine

# 3. sync pi (needs uv: https://docs.astral.sh/uv/)
uv run --directory ~/.claude/settings-sync sync pi   # writes pointers + inlined CLAUDE.md into ~/.pi/agent

# 4. authenticate, then use
pi            # then /login  (or: export ANTHROPIC_API_KEY=... etc.)
```

## Day-to-day: edit in ONE place

| Action | Where (in the repo) | Sync to pi |
|--------|---------------------|------------|
| Add a skill | `~/.claude/skills/<name>/SKILL.md` | commit → `git pull` → in pi: `/reload` (no re-sync needed) |
| Rename a skill | edit that one `SKILL.md` (or rename the dir) | as above |
| Add a command / prompt template | `~/.claude/commands/<name>.md` | as above |
| Add an extension | `~/.claude/pi/extensions/<name>.ts` | as above |
| Add a theme | `~/.claude/pi/themes/<name>.json` | as above |
| **Change pointers** | `~/.claude/pi/settings.json` | commit → `git pull` → `sync pi config` → `/reload` |
| **Change keybindings** | `~/.claude/pi/keybindings.json` | commit → `git pull` → `sync pi keybindings` → `/reload` |
| **Change global context** | `~/.claude/CLAUDE.md` or its `@` imports | commit → `git pull` → `sync pi context` (or `sync pi`) |

Skill discovery is **recursive** over directories containing `SKILL.md`, so dropping a new
`<name>/SKILL.md` is automatically picked up — no second touch, no symlink per skill. Skills
and commands are read directly by pi, so editing them needs only `/reload`, never a re-sync.

Notes on the `commands/` → pi prompt-template mapping:
- pi uses the **filename** as the command name (`resume-opencode.md` → `/resume-opencode`); the
  Claude `name:` frontmatter is ignored by pi.
- pi prompt discovery is **non-recursive** (top-level `.md` only), so keep commands as
  top-level files.
- Both use `$ARGUMENTS`, `$1`, `$@` for arguments — compatible.

## What stays machine-local (NOT synced)

- `~/.pi/agent/auth.json` — credentials
- `~/.pi/agent/sessions/` — session history
- `~/.pi/agent/bin/` — bundled `rg` binary
- `~/.pi/agent/models.json` — custom providers (per harness; e.g. a hosted model gateway)

Note: `~/.pi/agent/settings.json` is **not** machine-local — it's a wholesale copy of
`pi/settings.json`. Don't hand-edit it (changes are lost on next sync); edit the template.

## Re-running the sync

`sync pi` is idempotent. Re-run it after changing `pi/settings.json` or `CLAUDE.md` in
the repo. It wholesale-copies the pointers and re-inlines the context; identical files report
`unchanged`.

To target a different pi agent dir (e.g. a throwaway harness), use `--pi-dir`:
```bash
sync --pi-dir /tmp/glm-pi pi
```

Common flags (apply to `sync` and any subcommand, before the group name):
- `--check` — exit nonzero if drift detected, write nothing
- `--dry-run` — show what would change, write nothing
- `--force` — overwrite diverging derived files (context); pi config always overwrites
- `--verbose` / `-v` — show diffs for changed text artifacts

## Troubleshooting

- **New skill not showing?** Run `/reload` in pi (or restart). Confirm it has `SKILL.md`
  with `name` + `description` frontmatter. Dirs without `SKILL.md` are ignored silently.
- **Pointers lost / `/settings` clobbered them?** Re-run `sync pi config`.
- **Context stale after editing CLAUDE.md?** Re-run `sync pi context` (or `sync pi`).
- **Command name mismatch?** pi uses the filename, not the `name:` frontmatter.
- **Excluding a Claude-only skill** from pi: edit `pi/settings.json`, e.g.
  `"skills": ["~/.claude/skills", "!~/.claude/skills/caveman*"]` (arrays support globs + `!`).

## Files in this directory

- `settings.json` — pointer template (source of truth for resource locations)
- `keybindings.json` — pi keybindings (source of truth; wholesale-copied to ~/.pi/agent)
- `extensions/`   — pi extensions (TypeScript)
- `themes/`       — pi themes (JSON)
- `README.md`     — this file

See also [`settings-sync/README.md`](../settings-sync/README.md) and pi's own docs:
`pi /reload`, `/settings`, `--no-skills`, `--skill <path>`.
