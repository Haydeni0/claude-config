# claude-config

Backup of `~/.claude` config for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## What's tracked

- `CLAUDE.md` — global memory/instructions
- `settings.json` — permissions and plugin config
- `skills/` — custom skills
- `agents/` — custom subagents

## Install (new machine)

```bash
# If ~/.claude doesn't exist yet
git clone git@github-haydeni0:Haydeni0/claude-config.git ~/.claude

# If ~/.claude already exists (Claude Code was already run)
cd ~/.claude
git init
git remote add origin git@github-haydeni0:Haydeni0/claude-config.git
git fetch origin
git checkout -f main
```

## Update

```bash
cd ~/.claude && git add -A && git commit -m "update" && git push
```
