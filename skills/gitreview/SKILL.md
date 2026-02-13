---
name: gitreview
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
  - Bash(ls *)
  - Bash(find *)
---

Review GitHub pull request #$ARGUMENTS. Do NOT run tests, build commands, or attempt to fix anything — this is a read-only review.

## Steps

1. **Checkout the PR**

   ```
   gh pr checkout $ARGUMENTS
   ```

2. **Gather context**
   - `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
   - `gh pr diff $ARGUMENTS` to get the full diff
   - `gh pr checks $ARGUMENTS` to note CI status (for context only — do not act on failures)

3. **Deep review** — for each changed file:
   - Read the full file (not just the diff) to understand surrounding logic
   - Trace how the changes interact with callers, dependencies, and downstream consumers
   - Check whether the change breaks any implicit contracts or assumptions in adjacent code

4. **Check existing discussion**
   - `gh pr view $ARGUMENTS --comments` to see existing review comments

5. **Evaluate against these criteria** (skip any that don't apply):
   - **Correctness**: Bugs, edge cases, off-by-one errors, race conditions
   - **Security**: Injection, auth gaps, secrets, input validation
   - **Performance**: Unnecessary allocations, O(n²) where O(n) is possible, missing indexes
   - **Readability**: Naming, structure, unnecessary complexity
   - **Breaking changes**: API surface, backward compatibility, config changes
   - **Dependencies**: New dependencies justified and secure
   - **Missing coverage**: Untested paths that should have tests (note them, don't write them)

6. **Output format**

   ```
   ## Summary
   One-line description of what this PR does.

   ## CI Status
   Brief note on passing/failing checks. Do not investigate or fix failures.

   ## Findings

   ### Critical
   - [file:line] Description

   ### Major
   - [file:line] Description

   ### Minor / Nits
   - [file:line] Description

   ## Questions
   Things that are unclear or need author clarification.

   ## Verdict
   Approve / Request Changes / Comment — with brief justification.
   ```

Keep findings concise and actionable. Reference specific lines. Do not suggest stylistic changes unless they hurt readability.
