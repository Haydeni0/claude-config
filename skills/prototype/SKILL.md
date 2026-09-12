---
name: prototype
description: Use when a feature's main uncertainty is human judgement - how it looks or feels - and the design should be settled by building a throwaway artifact the human reacts to, before any spec or clean build. Covers terminal rendering, dashboards, API/class shape ("does this feel right to call"), and any visual or experiential design. Trigger phrases include "could we prototype this first?", "I want to see what it looks like", "let's try a few designs". Skip for logic-only features with settled design.
---

# prototype

Before committing to a design a human must judge, build a throwaway artifact from real material, let the human react to it, iterate until it survives the ugly cases, then discard the artifact and build cleanly from a spec that records what the artifact taught you.

**The one invariant: the human reacts to something concrete, in their real environment - never to a description.** Every guideline below serves that.

## When (and when not)

Prototype when the main uncertainty is human judgement, not mechanism - output is visual, or a system whose *shape* must feel right. When design is settled and only implementation is uncertain, skip straight to spec/plan: prototyping there is pure overhead.

The artifact's form follows its purpose: rendered output for visuals, worked usage examples for API/class design, a script driving the real system end-to-end for system design.

## Guidelines

**Ugly-but-real.** The smallest thing that puts the real experience in front of the human. Hardcode whatever isn't the point; skip layering, plumbing, tests. The only quality bar is "the human can judge the experience from it." Real material always - live data, real volumes, real hostile names - because synthetic fixtures hide exactly the edge cases you are prototyping to find.

**Rounds count only in the human's environment.** The medium the agent previews in is not the medium the human works in - display, scaling, fonts, and interaction all differ between them - so no round counts until the human has seen the real artifact where they work. Between rounds, self-serve mechanics freely: try variants internally, measure sizes, check edge cases. But react to one concrete thing at a time - presenting a menu of variants shifts design from taste to pick-listing.

**The exit gate is two-part: "looks good" AND "survived the ugly corpus."** Before sign-off, exercise empty results, single item, hostile inputs (names that break markup/escaping), extreme volumes, the worst-case row count. Happy-path rounds catch taste problems; the corpus catches correctness ones.

**Wipe the slate.** The prototype never graduates into product code - it is structurally compromised (no layering, no tests, hardcoded shortcuts) and its job is done once the spec exists. Discard it. Glancing at it for an implementation trick during the clean build is fine; *copying* is the failure mode the rule guards against.

**Then settle what pixels cannot.** Once taste is settled, interrogate the rest - flags, defaults, semantics, naming, edge-case behaviour - and write the spec from there. Pixels settle taste cheaply; questions settle what pixels cannot.

## Anti-patterns

- **Write code first, add tests later** - no: the prototype is discarded; product code is TDD-built fresh from the spec.
- **Proof-of-feasibility spike only** - no: feasibility is a bonus; the point is design judgement by a human on real material.
- **Synthetic-data demo** - no: real volumes and hostile names surface what fixtures hide.
- **Human reviews a description/proposal** - no: they react to the artifact, in their environment, every round.
