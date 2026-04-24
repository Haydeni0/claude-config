---
name: pr-description
description: Generate a PR description from the repo's PR template
argument-hint: "[PR number (optional)]"
allowed-tools:
  - Read
  - Grep
  - Glob
---

Generate a pull request description using the repo's structure (template if present) and the author's writing style. Output this to the user in markdown format so they can copy-paste it, or edit it themselves.

NEVER run `gh pr edit` or any command that modifies the PR, unless specifically instructed with the sentinel PUSH_AUTHORISED.

## PR template

!`cat .github/pull_request_template.md 2>/dev/null || cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || cat pull_request_template.md 2>/dev/null || echo "No PR template found."`

## PR metadata

!`gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,commits 2>/dev/null || git log --oneline -30`

## Current branch (if no open PR)

!`git branch --show-current`

## PR diff

!`gh pr diff $ARGUMENTS 2>/dev/null || git diff origin/main...HEAD`

## Instructions

1. **Analyze the context above**
    - Identify the purpose: feature, bugfix, refactor, experiment, etc.
    - Note any breaking changes, new dependencies, or config changes
    - If you need to read full files for surrounding logic (not just diffs), use the Read tool

## Author style

- Apply this style regardless of repository template. Templates can change, this style should stay consistent.
- Prefer one short lead sentence or short summary of changes followed by concrete bullets.
- Prefer bullet points for multi-part changes (typically 2-4 bullets).
- Keep bullets factual and implementation-specific (what changed and why), not placeholders.
- Avoid verbose prose when bullets communicate faster. Keep things concise.

1. **Print to the user**
    - Print the filled template as a fenced markdown block so the user can copy-paste it directly. Do NOT edit the PR itself. Nothing else — no commentary before or after.
    - If no PR template was found above, use a generic Description / Development Notes / Checklist structure.
    - Fill the template with concrete, accurate content based on the actual changes
      - Not every section of the template needs to be filled, for example if you're repeating yourself or not adding value to the reader.
    - Match the `## Author style` section above.
    - Be concise but informative. Prioritize `## Author style` over template wording/tone.
    - For checklists, check items that are clearly satisfied and leave others unchecked
