---
name: pr-review
description: Checkout and review a GitHub pull request
disable-model-invocation: true
argument-hint: <PR-number>
allowed-tools:
  - Bash(gh pr checkout *)
  - Bash(gh pr view *)
  - Bash(gh pr diff *)
  - Bash(gh pr checks *)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git merge-base *)
  - Read(*)
  - Grep(*)
  - Glob(*)
  - Bash(cat *)
  - Bash(head *)
  - Bash(tail *)
  - Bash(grep *)
  - Bash(rg *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(wc *)
  - Bash(uv sync*)
  - Bash(gh api repos/*/pulls/*/comments*)
  - Bash(gh api repos/*/pulls/*/reviews*)
---

Review GitHub pull request #$ARGUMENTS. Do NOT run tests, build commands, or attempt to fix anything — this is a read-only review.
You may run `uv sync` to set up the environment (and view the environment at `.venv`, for context on installed packages), but do NOT execute project code.
Forbidden: python, python3, pip, npm, node, make, cargo, docker run/build, pytest, or any command that runs/compiles project code.

## Steps

1. **Checkout the PR**

   ```bash
   gh pr checkout $ARGUMENTS
   ```

2. **Set up environment**

   ```bash
   uv sync
   ```

3. **Gather context**
   - `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
   - `gh pr diff $ARGUMENTS` to get the full diff
   - `gh pr checks $ARGUMENTS` to note CI status (for context only — do not act on failures)

4. **Deep review** — for each changed file:
   - Read the full file (not just the diff) to understand surrounding logic
   - Trace how the changes interact with callers, dependencies, and downstream consumers
   - Check whether the change breaks any implicit contracts or assumptions in adjacent code

5. **Check existing discussion**
   - `gh pr view $ARGUMENTS --comments` to see existing review comments

6. **Review and output**

   Apply the review criteria and output format from [code-review-guidelines](../code-review-guidelines/SKILL.md). Add a "CI Status" section after the Summary with a brief note on passing/failing checks (do not investigate or fix failures).

REMINDER: You have NO permission to run Python, pip, build tools, or any code execution. Only use the tools listed in allowed-tools.
