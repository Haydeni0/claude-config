# Test PR Core Workflow

Shared workflow for PR-scoped test analysis skills.

## Core Contract

- Decision scope: current branch/PR diff only.
- Context scope: broader codebase reads allowed to validate intent.
- No new dependencies unless user asks.
- Review-only skill. Never edit files.

## Base Scope Commands

Prefer `origin/main...HEAD` unless user specifies another base branch.

```bash
git diff --name-only origin/main...HEAD
git diff --stat origin/main...HEAD
git log --oneline origin/main..HEAD
```

## Universal Steps

```text
Shared progress
- [ ] 1) Identify changed files in target scope
- [ ] 2) Read changed files and relevant implementation context
- [ ] 3) Produce prioritized findings
- [ ] 4) Provide concrete plan with file-level actions
- [ ] 5) Provide numbered action list user can select from
- [ ] 6) Wait for user selection (no edits in this skill)
```

## Findings Format

Use findings first, severity ordered.

Response constraints:
- Use numbered lists for findings and plans (not bullet lists).
- Use priority buckets: `Critical`, `Major`, `Minor`.

```markdown
## Findings

### Critical
1. `path::symbol_or_test`: problem, risk, concrete fix.

### Major
1. `path::symbol_or_test`: problem, risk, concrete fix.

### Minor
1. `path::symbol_or_test`: improvement, concrete fix.

## Keep
1. `path::symbol_or_test`: valuable coverage or behavior contract.

## Plan
1. ...
2. ...
```

## Selection Gate

Ask user which numbered actions to apply elsewhere:

`Pick items to apply (for example: 1,3,4).`

## Non-Editing Rule

Do not modify files, run fix scripts, or apply tests in this skill. This skill is analysis and recommendation only.
