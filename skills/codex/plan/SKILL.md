---
name: plan
description: Turn an approved spec or rough non-trivial goal into executable slices with exact paths, contracts, decisions, and verification commands.
---

# /plan — executable slice plan

## Trigger

Use after an approved spec, or before implementation when the work has an
independent slice, a high-risk boundary, or an unresolved WHAT. Skip formal
planning for a closed existing-behavior packet whose paths and checks are clear,
even when it spans several files.

Formal planning may be closed inline in the current owner turn when the packet
is already closed. State the goal, exact paths, acceptance, and verification;
skipping a plan artifact never skips a required decision or user approval. One
slice may contain several small sequential substeps when they share the same
goal, acceptance, ownership, risk, verification, approval, and rollback
boundary.

## Plan structure

Record one goal, architecture boundaries, and a dependency-ordered list of
slices. Each slice must name exact `create` and `modify` paths plus optional
`test`/check paths, the relevant callers/producers/consumers, the observable
acceptance condition, and the smallest verification oracle with expected
exit/output. Keep signatures, schemas, and short test skeletons inline only
when they encode a cross-slice contract. Do not prescribe an algorithm that
belongs in `/impl`.

```yaml
slug: <kebab-case>
status: draft | approved
goal: <observable goal>
slices:
  - id: 1
    title: <slice>
    scope_authority: confirmed | user_approved_unresolved
    files:
      create: []
      modify: [<exact/path>]
      test: []  # optional existing test/check paths
    acceptance:
      A1: <observable condition>
    verification:
      scope: focused | integration | full
      type: unit_test | command | fixture | custom
      command: <shell command>
      proves: [A1]
      risk_predicate: null | <named risk>
      approved_by: null | lifecycle_owner | user
      expected_exit_code: 0
    line_budget: <1..200>
    public_contracts: []
    public_callers: []
    review_checkpoint: skip | candidate | required
    checkpoint_reason: null | <final-diff risk predicate>
    decision_needed: false
    options: []
```

The plan is approved only when every changed path has an owner slice, every
acceptance is covered by a proving oracle, and no placeholder or unresolved
WHAT remains. One oracle may prove several acceptance conditions. Do not create
a test solely to fill the optional `test` field.
`public_contracts` and `public_callers` are required when a public symbol or
artifact changes; discover callers with `git grep` rather than guessing.

Every slice must come from `/diagnose`'s current evidence state or another
explicit scope decision. `confirmed` needs no scope approval.
`user_approved_unresolved` names a still-unresolved uncertainty that the user
explicitly accepted. That approval applies only to this slice's current goal,
paths, risk, and lifecycle. If any of them changes, re-scope instead of carrying
the approval forward. A falsified hypothesis cannot own a slice.

Use `review_checkpoint: candidate` before implementation only when the
authorized scope may match an `/impl` predicate. At the checkpoint, the
lifecycle owner resolves it to `required` or `skip` from the final actual diff;
the planned label alone cannot dispatch a reviewer.

Before emitting `PLAN_READY`, the planning owner recalculates planning and
`spec-novelist` need from the final authorized actors, flows, and slices, then
applies the active `spec-novelist` ownership and timing contract. This is a
pre-implementation decision and does not depend on an actual diff. A controller
cannot run that pass on the planning owner's behalf or count its own advisory
pass as satisfying the gate.

## Risk and decisions

Surface user-facing flow choices, irreversible operations, user data,
permissions, database/schema, public contracts, external state, concurrency,
and migrations as explicit decisions. Internal HOW choices remain with the
implementer. Add a spike only for a concrete uncertainty whose failure would be
costly; routine work does not need one.

## Verification and handoff

Use the smallest relevant oracle: unit test, command, fixture comparison,
artifact existence, visual check, or custom command. An existing focused check
is sufficient when it proves the changed behavior; a new test is not required
by default. The implementer runs the declared commands and confirms the exact
changed paths are within the slice. A checkpoint or final review is conditional
on the final-diff predicates in `/impl`; the plan does not require a reviewer or
unverifiable transport metadata as a gate.

For `focused`, set `risk_predicate` and `approved_by` to `null`. Use
`integration` only for a named changed producer-consumer seam. Use `full` only
for a named risk that a focused or integration oracle cannot cover. Both broader
scopes require an exact command and explicit lifecycle-owner or user approval;
they are not implied by file count, production labels, prior incidents, or the
complexity of the surrounding system.

Before implementation, obtain user approval for any external work or changes to
user data, permissions, database/schema, public contracts, concurrency,
migrations, or other external state. Otherwise proceed once `status: approved`
and the packet is closed.
