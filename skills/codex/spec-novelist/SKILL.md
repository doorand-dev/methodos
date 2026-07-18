---
name: spec-novelist
description: Run one fresh-context actor and flow walk only for a spec with multiple actors or multiple flows.
---

# Spec Novelist

When a spec has multiple actors or flows, pass only the relevant spec text to
one fresh-context reader. Walk each named actor and list missing steps,
ambiguities, observable failure cases, authority boundaries, and state
transitions. Fold useful gaps into the spec.

A single-actor, single-flow spec does not invoke this agent. The current session
performs its own short actor/flow walk instead. The fresh pass is advisory and
needs no separate record or repeat review.
