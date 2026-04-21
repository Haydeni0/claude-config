---
name: meta-review-guidelines
description: Criteria for meta-reviewing an existing code review. Defines the 6 validation checks, per-finding verdict taxonomy, and guardrails. Output format is reused from code-review-guidelines.
user-invocable: false
---

## Input contract

Caller provides:

- Review v1 in `code-review-guidelines` output format (markdown string).
- Base ref (e.g. `origin/main`) for diffing.

## Procedure

1. **Load ground truth**
   - `git diff $BASE..HEAD` for the full diff.
   - For each finding, `Read` the cited file around the cited line.

2. **Per-finding verdict** - for each finding in v1, apply in order:
   - **Citation check:** the line exists and code at that location matches the claim. If not → `drop`.
   - **Accuracy check:** the claim is technically correct. If not → `drop`.
   - **Severity check:** Critical/Major/Minor label matches impact. If mismatch → `reclassify`.
   - **Noise check:** stylistic or unactionable per `code-review-guidelines`. If yes → `drop`.
   - **Dedup:** same issue as an earlier finding. If yes → `merge`.
   - Else → `keep` (optionally `edit` for clarity).

3. **False-negative sweep** - scan the diff independently. Note any issues v1 missed. Add as new findings with `file:line` citations.

4. **Emit v2** - same output format as `code-review-guidelines`. Recompute the Verdict from remaining findings. Keep the Summary unchanged unless it is incorrect.

## Guardrails

- If more than 50% of v1 findings are dropped, append one line to the Summary: `Meta-review removed N of M findings.`
- Never add a finding without a `file:line` citation.
- Respect the "do not flag pre-existing issues" rule from `code-review-guidelines`.
- Read-only. Do not modify any repository file.
- Single pass. Do not loop.

## Output

Return the final review (v2) as a markdown string in `code-review-guidelines` output format. Nothing else.
