---
name: prdesc
description: Generate a PR description from the repo's PR template
disable-model-invocation: true
argument-hint: <PR number>
allowed-tools:
  - Bash(gh pr view *)
  - Bash(gh pr diff *)
  - Bash(git log *)
  - Bash(git merge-base *)
  - Bash(ls *)
  - Bash(find *)
---

Generate a pull request description for PR #$ARGUMENTS based on the repo's PR template. Output this to the user in markdown format so they can copy-paste it, or edit it themselves.

**NEVER run `gh pr edit` or any command that modifies the PR.**

## Steps

1. **Find the PR template**

    Search the repo for a PR template in common locations:
    - `.github/pull_request_template.md`
    - `.github/PULL_REQUEST_TEMPLATE.md`
    - `.github/PULL_REQUEST_TEMPLATE/*.md`
    - `pull_request_template.md` (repo root)
    If no template is found, use a generic Description / Development Notes / Checklist structure.

2. **Gather PR context**
    - `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,commits`
    - `gh pr diff $ARGUMENTS` to see all changes
    - `git log` for the PR's commits to understand the narrative

3. **Understand the changes**
    - Read the full changed files (not just diffs) to understand surrounding logic
    - Identify the purpose: feature, bugfix, refactor, experiment, etc.
    - Note any breaking changes, new dependencies, or config changes

4. **Print to the user**
    - Print the filled template as a fenced markdown block so the user can copy-paste it directly. Do NOT edit the PR itself. Nothing else — no commentary before or after.
    - Fill the template with concrete, accurate content based on the actual changes
      - Not every section of the template needs to be filled, for example if you're repeating yourself or not adding value to the reader.
    - Be concise but informative — match the style guidance in the template
    - For checklists, check items that are clearly satisfied and leave others unchecked
