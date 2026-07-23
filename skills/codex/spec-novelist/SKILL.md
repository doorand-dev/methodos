---
name: spec-novelist
description: Run one fresh-context actor and flow walk only for a spec with multiple actors or multiple flows.
---

# Spec Novelist

The planning owner owns this pass. After user WHAT decisions are closed and
immediately before emitting `PLAN_READY`, a multi-actor or multi-flow planning
owner sends only the relevant spec text to exactly one fresh-context reader
without inherited turns (`fork_turns="none"`). Walk each named actor and list
missing steps, ambiguities, observable failure cases, authority boundaries, and
state transitions. The planning owner folds useful findings into the packet and
emits the revised `PLAN_READY` or `PLAN_READY_V2`.

If the pass opens a user WHAT or changes scope, the planning owner returns to
that decision before emitting the packet. A controller does not run this pass on
the planning owner's behalf. A controller-run pass is advisory evidence only
and does not satisfy this pre-approval gate.

A single-actor, single-flow spec does not invoke this agent. The current session
performs its own short actor/flow walk instead. The pass is required for a
multi-actor or multi-flow spec; its findings are advisory and need no separate
record or routine repeat review.
