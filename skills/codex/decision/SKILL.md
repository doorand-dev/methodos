---
name: decision
description: Converge an option comparison, workaround, irreversible operation, public interface, or user-delegated decision.
---

# /decision

Use this skill when options materially differ, a change is hard to reverse, or
the user asks the agent to decide. For a closed, reversible implementation,
answer directly.

1. State what changes for the user or operator and what remains uncertain.
2. Compare the smallest viable options, including near-term cost and ongoing
   maintenance cost. Prefer the option that preserves existing contracts and
   has a concrete test.
3. Ask for approval before external work, user data, permissions, database or
   schema changes, public interfaces, concurrency/migrations, or other external
   state. Do not silently choose between materially different user outcomes.
4. Persist an ADR only when the decision is hard to reverse, surprising without
   context, or a real trade-off that a future maintainer must know. If none
   applies, close in the conversation; do not add a WHY comment or report just
   to record routine work.

Use `docs/adr/` (or the workspace decision configuration) for a durable ADR.
Keep it short: decision, alternatives considered, consequence, and re-evaluation
condition. Tests and exact changed paths are the completion evidence.
