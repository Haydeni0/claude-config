---
name: tempfile
description: Use when the user wants to dump something from chat - a PR review, a summary, a code block, notes - to a temporary markdown file at the workspace root
---

# Tempfile

Dump content from chat to a temp markdown file at the workspace root.

## Steps

1. **Identify content.** What does the user want saved? Usually the last substantial thing in chat (PR review, summary, notes). If `$ARGUMENTS` names it, use that. If `$ARGUMENTS` contains the content itself, use it directly.

2. **Pick suffix.** Choose a kebab-case slug from the content/context. e.g. `pr-review`, `auth-bug-notes`, `meeting-summary`. Filename = `TEMP-<suffix>.md`.

3. **Write the file.** Path = `<CWD>/TEMP-<suffix>.md`. Raw content only - no header, no timestamp, no metadata, no `# TEMP` line. Overwrite silently if a file with that name exists.

4. **Report.** Print the absolute path and a one-line confirmation of what was dumped.

## Ask-back

If you genuinely cannot tell what content the user wants dumped, or the suffix is truly ambiguous, ask one clarifying question. Do not ask for mild uncertainty - make a reasonable guess and write the file.

## Rules

- Filename: `TEMP-` prefix + kebab-case suffix + `.md`. Lowercase, alnum + hyphens only. No spaces, no special chars.
- Location: workspace root = current working directory. Not `.claude/`, not git root.
- Content: raw only. Exactly what would've gone in chat.
- Overwrite: always create fresh. Temp files are throwaway - reuse means same context re-dumped.
- Suffix override: if `$ARGUMENTS` clearly names the file (e.g. "save it as review"), use that name. Otherwise infer from content.
