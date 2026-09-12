# Contributing to <repo name>

<This repo is built agent-first: features are implemented by AI coding
agents against a written prompt, then reviewed and verified by a human.
The unit of contribution here is **a well-specified prompt, not a pull
request**. - OR the conventional opposite: "PRs welcome; read this first
for the standards CI and review will hold them to." Pick one stance and
delete the other.>

## How to contribute a feature

1. [Open a GitHub issue - not a PR. / Open a PR against main; CI runs
   `uv run task check` and review holds you to the standards below.]
2. [Who executes it and what the loop looks like.]
3. You review the result [on the PR that lands it; the discussion lives
   in the issue].

Bug reports follow the same shape - skip the acceptance-criteria
formality, but include the command you ran, what you saw, and what you
expected.

## Feature-request template

Write it as a prompt an agent could execute directly. The quality bar:
someone who has never spoken to you could read it and build the right
thing with no follow-up questions.

```markdown
## Feature: <one-line summary>

### Problem
What you're trying to do, and what's painful about the current commands
today. One short paragraph.

### Proposed <command/API surface>
The exact surface you expect:

    <exact invocation sketch>

Show the flags and defaults you want, and what each should do.

### Expected output
Paste a sketch of the output you want to see - a rough table, tree or
chart is fine. [For anything wrapping an external CLI/API: include the
underlying command(s) and flags it should wrap, and paste a real sample
of their output if you can.]

### Acceptance criteria
- [ ] Given <input/state>, running <command> shows <result>
- [ ] ...
- Specific, checkable statements. An agent or reviewer can run each one.
- Include edge cases: empty results, no matching records, missing tools.
```

### What makes a good request

- **One feature per issue.** A "cluster dashboard" is five issues.
- **Show, don't describe.** A pasted sketch of the output is worth more
  than a paragraph of prose.
- **State the acceptance criteria as things a runner can verify** - not
  "should look nice" but "shows 4 columns: user, nodes, gpus, cap".
- **Repro-first for bugs**: paste the actual failing output and the exact
  command that should pass once fixed.

## Code standards

If you do open a PR, it will be held to what the repo already enforces:

- `uv run task check` passes (lint, typecheck, tests).
- [New code follows the structure/rules in AGENTS.md - name the specific
  section, e.g. "the domain structure: commands -> queries -> cli seam
  -> render".]
- [Behavioural tests for anything new; real-payload captures in
  `tests/data/` when a new external JSON/data shape is introduced;
  golden-output refresh via the documented env var, reviewed like code.]
- [Read MEMORY.md before touching <the historically gnarly areas> -
  it holds the verified gotchas.]

## Releases

[If release automation exists, one short paragraph: e.g. "bump
`version` in pyproject.toml, commit to main, push - the Release
workflow tags, builds, and publishes. Users install @latest."] [Cut if
releases are manual or absent.]
