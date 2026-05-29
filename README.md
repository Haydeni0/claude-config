# claude-config

Backup of `~/.claude` config for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

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

## Install (new machine)

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
