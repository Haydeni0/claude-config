# goose

Base config for [goose](https://goose.dev), synced into `~/.config/goose` by `settings-sync`.

## What's tracked

| File | Purpose |
|---|---|
| `config.yaml` | Base goose config (telemetry, extensions, search paths) |
| `custom_providers/*.json` | Custom provider definitions (OpenAI/Anthropic/Ollama compatible endpoints) |

## What goose reads natively (no sync needed)

goose has backward-compat discovery paths for `~/.claude`:

| Source | Goose discovers? | Path |
|---|---|---|
| `~/.claude/skills/` | Yes | `~/.claude/skills/` (compat path) |
| `~/.claude/agents/` | Yes | `~/.claude/agents/` (compat path) |
| `~/.claude/commands/` | No | goose slash commands are `config.yaml` entries mapping to recipe files (different format) |

Agent frontmatter note: goose only reads `name`, `description`, `model` from agent frontmatter. Claude Code keys (`tools`, `disallowedTools`, `skills`) are ignored - goose does not enforce tool restrictions from agent files.

## What settings-sync derives

| Source in `~/.claude` | Target in `~/.config/goose` | Mechanism |
|---|---|---|
| `CLAUDE.md` + `@` imports | `.goosehints` | `@` imports inlined, `@skills/<n>` rewritten to `the \`<n>\` skill` (same transform as opencode `AGENTS.md` and pi `CLAUDE.md`) |
| `goose/config.yaml` | `config.yaml` | copy; refuses to clobber a diverging file without `--force` (machine-specific settings set via `goose configure` or env vars are preserved) |
| `goose/custom_providers/*.json` | `custom_providers/*.json` | per-file copy; orphans warned (removed with `--force`) |

## Usage

```bash
# via sync.sh (runs settings-sync + installs)
bash ~/.claude/sync.sh

# granular
uv run --directory ~/.claude/settings-sync sync goose            # all goose steps
uv run --directory ~/.claude/settings-sync sync goose hints     # .goosehints only
uv run --directory ~/.claude/settings-sync sync goose config     # config.yaml only
uv run --directory ~/.claude/settings-sync sync goose providers  # custom_providers/ only
```

After editing `~/.claude/CLAUDE.md` or `goose/`, re-run `sync goose` (or `sync`).
