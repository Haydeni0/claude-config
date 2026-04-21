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
  - Agent(*)
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

6. **Produce review v1**

   Apply the review criteria and output format from [code-review-guidelines](../code-review-guidelines/SKILL.md). Add a "CI Status" section after the Summary with a brief note on passing/failing checks (do not investigate or fix failures). Hold this as review v1 - do NOT output it to the user yet.

7. **Meta-review pass**

   - Record the base ref used against the PR target. If not already computed: `BASE=$(git merge-base HEAD origin/$(gh pr view $ARGUMENTS --json baseRefName -q .baseRefName))`.
   - Use the `Agent` tool with `subagent_type: meta-reviewer`. Pass review v1 (full markdown) and the base ref in the prompt.
   - Output the meta-reviewer's return value (v2) as the final review. If the meta-reviewer errors, output v1 with a one-line note appended to its Summary: `Meta-review unavailable.`

REMINDER: You have NO permission to run Python, pip, build tools, or any code execution. Only use the tools listed in allowed-tools.
