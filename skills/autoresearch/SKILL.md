# Claude Autoresearch — Overview

**Claude Autoresearch** is an autonomous iteration system inspired by Karpathy's autoresearch framework, designed to apply goal-directed loops to any task requiring repeated improvement cycles.

## Core Mechanism

The system operates through a structured loop:

1. **Review** current state and history
2. **Ideate** the next focused change
3. **Modify** one aspect in scope
4. **Commit** changes to git
5. **Verify** using mechanical metrics
6. **Decide** whether to keep or discard
7. **Log** results and repeat

As stated: "Loop until done — Unbounded: loop until interrupted. Bounded: loop N times then summarize."

## Three Main Commands

- **`/autoresearch`** — Runs the autonomous iteration loop
- **`/autoresearch:plan`** — Interactive wizard converting goals into executable configurations
- **`/autoresearch:security`** — Comprehensive security audit using STRIDE threat modeling and OWASP Top 10 taxonomy

## Key Characteristics

The system emphasizes **mechanical verification** over subjective judgment, **atomic changes** for clarity, and **automatic rollback** on failure. It works across domains—backend code, frontend UI, ML training, content, performance optimization, and refactoring—by adapting metrics while maintaining universal principles.

Users can run unbounded loops (continuous until manual interruption) or bounded loops using `/loop N` syntax for controlled iteration counts.
