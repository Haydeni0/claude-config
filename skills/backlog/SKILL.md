---
name: backlog
description: Use when the user defers a side topic mid-work or asks to see or close deferred items. Capture triggers - "one other thing", "one more thing", "before I forget", "side note", "side topic", "save this for later", "park it for later", "note this down", "just noting", "come back to this", "talk about this later", "at some point", "things to pick up on". Recall triggers - "backlog", "what's next", "clear out the backlog", "next session". Never trigger on "jot" - the user never uses it.
---

# Backlog

Append deferred side topics to `.claude/backlog.md` at the git root so they survive to a later session. Chat-only acknowledgments rot with scrollback; the file is the record.

## When

- User defers a topic mid-work: "one other thing - we should also X, but finish Y first"
- User notices a problem but wants current work to finish first: "I don't like this design, but let's finish X"
- User asks for the backlog: "what's next", "check the backlog", "clear out the backlog"
- User closes items: "that's done", "/backlog done 3"

## Capture

1. Resolve target: git root + `.claude/backlog.md`. If cwd is not a git repo, cwd + `.claude/backlog.md`.
2. Create with this template if missing:

   ```markdown
   # Backlog

   Deferred items for this project. Surfaced when starting work here; picked up on request.

   ## Open
   ```

3. Next ID = max existing `#N` in file + 1. IDs are never reused, so deletions don't renumber.
4. Append under `## Open`:

   ```markdown
   - #7 [2026-08-31] <text>
   ```

   Longer thoughts get continuation lines indented under the bullet. Concise by default; no hard cap.
5. Mention in chat in one clause ("noted to backlog as #7") and continue the interrupted work without waiting.

## Recall

`/backlog` bare, "what's next" → print open items, ID + one line each. Don't stop at listing: recommend what to pick up next (judge by relevance to current work, age, size) and say why. If an item needs clarification before it's actionable, ask about it - one question at a time.

If the trigger arrives mid-flow (interview, review, task), resume the pending step exactly after capture/recall - a deferral is never an answer, decision, or advance signal.

## Close

- `/backlog done <id>` → move the line to a `## Done` section (create after Open if missing), keeping ID and date.
- `/backlog clear` → delete the `## Done` section contents.
- Closing is user-disposed: when the agent notices an open item was clearly addressed by work just done, it suggests closing ("#3 looks covered - close it?") and moves it only on confirmation. User-initiated close is unconditional.

## Rules

- Everything deferred goes here. No routing to QUESTIONS.md or similar unless the user names that file.
- "jot" is not a trigger word - the user never uses it.
- No git operations on this file. It shows as untracked in git status; that is intended.
- When starting work in a project that has a backlog, surface open items before diving in (see the backlog rule in global CLAUDE.md).
