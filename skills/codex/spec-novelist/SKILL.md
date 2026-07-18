---
name: spec-novelist
description: Run one optional fresh-context narrative pass for a multi-actor or multi-flow spec.
---

# Spec Novelist

When a new spec has several actors or flows, pass only the relevant spec text to
one fresh-context reader. Ask it to walk each named actor and list missing steps,
ambiguities, and observable failure cases. Fold useful gaps into the spec and
return the result to the caller. A single-flow change can skip this pass.

The pass is advisory: no report file, hash, session/model/effort attestation, or
repeat review is required. If fresh-context dispatch is unavailable, state that
the narrative pass was skipped and continue with the local spec checks.
