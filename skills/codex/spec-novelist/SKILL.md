---
name: spec-novelist
description: Walk a multi-actor or multi-flow spec from each actor's perspective; use the current session by default and a fresh reader only when independent context materially helps.
---

# Spec Novelist

When a new spec has several actors or flows, the current session first walks
each named actor and lists missing steps, ambiguities, and observable failure
cases. Fold useful gaps into the spec. A single-flow change can skip this pass.

Use one fresh-context reader only when actor interactions, authority or state
transitions, or failure recovery make an independent read materially useful, or
when the user requests it. Pass only the relevant spec text. The pass is
advisory and needs no separate record or repeat review.
