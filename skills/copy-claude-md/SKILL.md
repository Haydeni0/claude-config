---
name: copy-claude-md
description: Use when the user wants to sync CLAUDE.md and its imports to Cursor's global rules, or when CLAUDE.md has been updated and Cursor should reflect the changes.
---

# Copy Claude MD

Compiles `~/.claude/CLAUDE.md` (resolving all `@` imports) into a flat string and copies it to the clipboard, ready to paste into Cursor's global rules.

## Steps

1. Read `~/.claude/CLAUDE.md`
2. For each `@path` import line, read the referenced file and inline its content (replacing the `@` line)
3. Copy compiled output to clipboard with `pbcopy`
4. Tell the user to paste into: **Cursor Settings > General > Rules for AI**

## Why not automate fully

Cursor stores global rules in the cloud (not a local file), so there is no programmatic write path. The clipboard + paste approach is the only reliable method.

## Implementation

Run `sync.sh` from this skill directory, then paste in Cursor:

```bash
bash ~/.claude/skills/copy-claude-md/sync.sh
```

## Frontmatter

User rules support frontmatter. The compiled output includes `alwaysApply: true` so the rules apply to every session.
