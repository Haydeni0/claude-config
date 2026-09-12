---
summary: "Agent long-term memory - <topic> lessons learned"
read_when:
  - Starting work in this repo
  - Hitting a gotcha that might recur
  - <adding a new domain / chart / command - the repo's repeat triggers>
---

# MEMORY.md - <repo name>

Long-term memory for AI agents working in this repo. Read at session
start; append to when you discover or fix something non-obvious. Don't
duplicate AGENTS.md rules here - an entry expands on a rule with the
evidence (what broke, the fix, the commit), since that provenance is the
value this file adds over the rule alone.

Rules:
- One entry per learning, newest at top.
- Date + one-line summary as a `###` heading, then the detail.
- Only verified facts you confirmed this session - no guesses.
- Reference the commit that fixed it, where it exists.
- Prune: merge or drop entries whose constraint no longer holds; when
  an entry's evidence stabilizes into a standing rule, promote it to
  AGENTS.md and drop the entry.

## Learnings

### <YYYY-MM-DD> - <one-line summary>
<What broke, the mechanism (why it happened), the fix, and the rule that
generalizes it. Enough that a future session skips the rediscovery.>
