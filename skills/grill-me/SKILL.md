---
name: grill-me
description: Use when stress-testing a plan or design before implementation - challenges assumptions, sharpens terminology, resolves dependencies between decisions one at a time
metadata:
  source: https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask one question at a time, waiting for feedback before continuing.

If a question can be answered by exploring the codebase, explore it instead of asking.

## During the session

**Sharpen fuzzy language** - when vague or overloaded terms appear, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User?"

**Discuss concrete scenarios** - stress-test domain relationships with specific edge-case scenarios that force precision about boundaries.

**Cross-reference with code** - when the user states how something works, check whether the code agrees. Surface contradictions: "Your code does X, but you just said Y — which is right?"
