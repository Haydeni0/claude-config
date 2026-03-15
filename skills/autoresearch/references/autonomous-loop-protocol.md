# Autonomous Loop Protocol Summary

This document outlines a structured iterative research loop with two modes:

**Loop Modes:**
- Unbounded (continuous until manual stop)
- Bounded (exactly N iterations)

**Core Workflow (8 Phases):**

1. **Review** — Assess current state, recent changes, and results log
2. **Ideate** — Strategically select the next modification based on priority (fixes first, then exploit successes, explore new approaches)
3. **Modify** — Make one atomic, clearly describable change
4. **Commit** — Git commit before verification for clean rollback capability
5. **Verify** — Run verification command and extract metrics
6. **Decide** — Keep, discard, or attempt crash recovery with clear logic
7. **Log Results** — Record iteration details in TSV format
8. **Repeat** — Continue per mode rules

**Key Principles:**

The protocol emphasizes "never assume—always verify" by reading full state each iteration. Changes must be singular and attributable. The guidelines discourage repeating failed experiments and chasing marginal gains through complexity.

**Crash Recovery:** Syntax errors receive immediate fixes. Runtime errors allow up to 3 fix attempts. Resource exhaustion triggers reversion and simplified retry.

**Communication Stance:** The system should not ask permission to continue in unbounded mode—it persists autonomously. Brief status updates appear every ~5 iterations; full summaries print only upon bounded completion.
