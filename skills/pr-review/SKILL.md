---
name: pr-review
description: Checkout and review a GitHub pull request
disable-model-invocation: true
argument-hint: <PR-number> [--since <commit>]
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
  - Agent(*)
---

Parse `$ARGUMENTS` as: `<PR-number> [--since <commit>]`

- `PR_NUMBER`: the PR number (required)
- `SINCE`: the commit passed to `--since`, if present (optional)

Do NOT run tests, build commands, or attempt to fix anything — this is a read-only review.
You may run `uv sync` to set up the environment (and view the environment at `.venv`, for context on installed packages), but do NOT execute project code.
Forbidden: python, python3, pip, npm, node, make, cargo, docker run/build, pytest, or any command that runs/compiles project code.

## Steps

1. **Checkout the PR**

   ```bash
   gh pr checkout $PR_NUMBER
   ```

2. **Set up environment**

   ```bash
   uv sync
   ```

3. **Gather context**
   - `gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
   - `gh pr checks $PR_NUMBER` to note CI status (for context only — do not act on failures)

4. **Compute base ref** (only when `--since` was provided)

   ```bash
   BASE=$(git merge-base $SINCE HEAD)
   ```

   Skip this step if `--since` was NOT provided — `gh pr diff` is used instead (see step 6).

   > **Why not `git merge-base` for the default path?** Repos using squash-merge or rebase-merge cause `git merge-base HEAD origin/<base>` to return a commit older than the PR's true base, pulling in changes already on the base branch. `gh pr diff` uses GitHub's server-side diff and is always correct.

5. **Check diff size** (only when `--since` was NOT provided)

   Use `changedFiles`, `additions`, and `deletions` already fetched in step 3. No extra command needed.

   If the diff exceeds 500 lines or 10 files, ask the user:
   > "This diff is large (X files, Y lines). Want me to focus on a specific area, file pattern, or concern? Or proceed with full review?"

   - If the user narrows scope, note the requested paths/patterns for step 6.
   - If the user says proceed, continue as normal.

6. **Get diff**

   If `--since` was provided:
   ```bash
   git diff $BASE..HEAD
   ```

   Otherwise:
   ```bash
   gh pr diff $PR_NUMBER
   ```

   If the user narrowed scope in step 5:
   - To exclude paths: `gh pr diff $PR_NUMBER -e '<glob-pattern>'`
   - To focus on specific files: get the full diff, then use the Read tool on only the files in scope for step 7.

7. **Deep review** — for each changed file in scope:
   - Read the full file (not just the diff) to understand surrounding logic
   - Trace how the changes interact with callers, dependencies, and downstream consumers
   - Check whether the change breaks any implicit contracts or assumptions in adjacent code

8. **Check existing discussion**
   - `gh pr view $PR_NUMBER --comments` to see existing review comments

9. **Produce review v1**

   Apply the review criteria and output format from [code-review-guidelines](../code-review-guidelines/SKILL.md). Add a "CI Status" section after the Summary with a brief note on passing/failing checks (do not investigate or fix failures). Hold this as review v1 - do NOT output it to the user yet.

10. **Meta-review pass**

    - Use the `Agent` tool with `subagent_type: meta-reviewer`. Pass review v1 (full markdown) and the base ref in the prompt:
      - If `--since` was provided: use `$BASE` (the merge-base SHA from step 4).
      - Otherwise: use `origin/<baseRefName>` (e.g. `origin/main`) so the meta-reviewer's diff sweep matches the correct PR diff.
    - Output the meta-reviewer's return value (v2) as the final review. If the meta-reviewer errors, output v1 with a one-line note appended to its Summary: `Meta-review unavailable.`

REMINDER: You have NO permission to run Python, pip, build tools, or any code execution. Only use the tools listed in allowed-tools.
