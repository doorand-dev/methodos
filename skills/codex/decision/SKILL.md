---
name: decision
description: Converge an option comparison, workaround, irreversible operation, public or user-visible behavior change, ambiguous user-visible referent, or user-delegated decision.
---

# /decision

Use this skill when options materially differ, a change is hard to reverse, or
the user asks the agent to decide. For a closed, reversible implementation,
answer directly.

## User-visible behavior authority

**BEHAVIOR-AUTH-001** — Safety, validation, persistence, idempotency, retry,
exactly-once behavior, and tests constrain implementation HOW but do not
authorize a different user-visible WHAT. Apply this gate when the proposed
observable behavior differs from an explicitly approved or established baseline
in action meaning, navigation/timing, visible state or copy, workflow ordering,
editing/source authority, fallback/retry, or output name/shape/cardinality, or
when a user-visible visual, layout, or output referent remains ambiguous.

An exact evidenced restoration may stay on the focused repair path. Otherwise
the lifecycle owner presents bounded alternatives and obtains user approval
before implementation; an ambiguous baseline returns `NEEDS_USER`. Current
code, tests, and generated artifacts are implementation evidence, not approval.

Before planning, routing, or implementing a user-visible visual, layout, or
output change, resolve the referenced object. If a bounded read-only check still
leaves multiple plausible layers, objects, actions, or source authorities,
restate the understood actor, object, scope, and reference and obtain explicit
confirmation. Until then, keep the scope unresolved and return `NEEDS_USER`;
do not promote one interpretation to `confirmed`. Skip this confirmation when
the referent and scope are unique or the work is an exact evidenced restoration.
File, layout, or channel count alone is not a trigger.

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
