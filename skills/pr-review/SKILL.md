---
name: pr-review
description: Checkout and review a GitHub pull request
disable-model-invocation: true
argument-hint: <PR-number> [--since <commit>]
allowed-tools:
  - Bash(gh pr checkout *)
  - Bash(gh pr view *)
  - Bash(gh pr checks *)
  - Bash(git diff *)
  - Bash(git fetch *)
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

4. **Fetch base branch**

   ```bash
   git fetch origin <baseRefName>
   ```

   This ensures `origin/<baseRefName>` is current before computing diffs. Use the `baseRefName` from step 3.

5. **Compute base ref** (only when `--since` was provided)

   ```bash
   BASE=$(git merge-base $SINCE HEAD)
   ```

   Skip this step if `--since` was NOT provided.

6. **Get diff**

   If `--since` was provided:
   ```bash
   git diff $BASE..HEAD
   ```

   Otherwise:
   ```bash
   git diff origin/<baseRefName>...HEAD
   ```

   Three dots (`...`) = diff from merge-base, matching GitHub's PR Changes tab. Never two dots (`..`) — that compares tips directly and pulls in unrelated commits from branches that haven't rebased onto main.

   **Enumerate changed files** (for step 8):
   ```bash
   git diff --name-only origin/<baseRefName>...HEAD
   ```

7. **Deep review** — for each file listed by step 6's `--name-only` output:
   - Read the full file (not just the diff) to understand surrounding logic
   - Trace how the changes interact with callers, dependencies, and downstream consumers
   - Check whether the change breaks any implicit contracts or assumptions in adjacent code

8. **Check existing discussion**
   - `gh pr view $PR_NUMBER --comments` to see existing review comments

9. **Produce review v1**

    Apply the review criteria and output format from [code-review-guidelines](../code-review-guidelines/SKILL.md). Add a "CI Status" section after the Summary with a brief note on passing/failing checks (do not investigate or fix failures). Hold this as review v1 - do NOT output it to the user yet.

10. **Meta-review pass**

    - Use the `Agent` tool with `subagent_type: meta-reviewer`. Run it in the foreground and wait for its return value inline. Do NOT set `run_in_background` and do NOT schedule a wakeup — the call returns when the agent finishes, and a redundant wakeup produces a duplicate "already done" turn.
    - Pass review v1 (full markdown) and the base ref in the prompt:
      - If `--since` was provided: use `$BASE` (the merge-base SHA from step 5).
      - Otherwise: use `origin/<baseRefName>` (e.g. `origin/main`) so the meta-reviewer's diff sweep uses the same three-dot base.
    - In the prompt, instruct the meta-reviewer to return **only** the cleaned review markdown (Summary through Verdict) with no preamble, working notes, or commentary.
    - The meta-reviewer's return value (v2) is the final review. If the meta-reviewer errors, use v1 with a one-line note appended to its Summary: `Meta-review unavailable.`

11. **Deliver one clean artifact**

    - Write the final review (v2, or v1 if the meta-reviewer errored) to `pr-<PR_NUMBER>-review.md` in the repo root. This file is the single output — strip any leaked agent working notes so it contains only the review markdown.
    - In chat, emit ONLY a one-line pointer: the file path and the Verdict line (e.g. `Review written to pr-405-review.md — Verdict: Comment`). Do not paste the review body or wrap it in narration; the file is the clean output.

