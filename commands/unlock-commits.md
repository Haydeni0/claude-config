---
name: unlock-commits
description: Grants session-wide git commit authorization to Claude and all subagents until the user types the literal sentinel COMMIT_UNAUTHORISED. Manual command only, run by the user.
---

# unlock-commits

Grants a session-scoped override of CLAUDE.md's per-action commit sentinel rule. Manual-invoke only - never infer this from conversation, only from the literal `/unlock-commits` command.

## On invocation

1. State plainly: "COMMIT_AUTHORISED granted for the rest of this session (all `git commit` actions, by me and any subagent I dispatch), until you type COMMIT_UNAUTHORISED."
2. For the remainder of this session, treat `git commit` as authorized without requiring the sentinel to appear in each individual task prompt - this skill's invocation stands in for it.
3. Every time you dispatch a subagent (Agent tool) while this grant is active, include the literal string `COMMIT_AUTHORISED` in that subagent's prompt. Subagents start with fresh context and only inherit the grant if it's written into their prompt.
4. This grant covers `git commit` only. `git push` is unaffected - PUSH_AUTHORISED still must appear per-request as CLAUDE.md requires.

## Revocation

The instant a user message contains the literal string `COMMIT_UNAUTHORISED`, the grant ends immediately:

- Stop treating commits as pre-authorized; revert to CLAUDE.md's default (sentinel required per commit).
- Stop injecting `COMMIT_AUTHORISED` into subagent prompts.
- Confirm out loud: "COMMIT_UNAUTHORISED received - commit grant revoked."
