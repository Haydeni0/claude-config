---
name: grill-me
description: Use when stress-testing a plan or design before implementation - challenges assumptions, sharpens terminology, resolves dependencies between decisions one at a time
metadata:
  source: https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

Ask one question at a time, waiting for feedback before continuing.

## Question format

Every question must follow this structure:

**Q[N]:** prefix each question with its sequential number (Q1, Q2, Q3, ...).

1. **The question** - prefer concise; add a sentence of context only when the tradeoff genuinely needs it
2. **Options** - provide options in whatever format makes sense, even for open-ended questions (generate plausible candidates).
3. **Recommend:** - always present, always explicitly labeled. States your recommendation and the one-line reason.

## Responding to answers

- User says **yes / ok / y / sure**: treat your recommendation as accepted. Move to the next question silently - no echo, no confirmation.
- User gives **free text override**: incorporate it and move on. Only echo back if the override is ambiguous.

## During the session

**Sharpen fuzzy language** - when vague or overloaded terms appear, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User?"

**Discuss concrete scenarios** - stress-test domain relationships with specific edge-case scenarios that force precision about boundaries.

**Cross-reference with code** - when the user states how something works, check whether the code agrees. Surface contradictions: "Your code does X, but you just said Y — which is right?"

If a question can be answered by exploring the codebase, explore it instead of asking.

## Ending the session

When all major branches are resolved, produce a **decision log** - one line per decision:

```
Decision: [what was decided] - [one-line rationale]
```

Example:
```
Decision: JWT over sessions - stateless, fits the distributed deployment
Decision: 1h token expiry - short window limits blast radius if token leaked
Decision: httpOnly cookie for refresh token - XSS-safe, JS cannot read it
```
