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
slices. Each slice must name exact `create`, `modify`, and `test` paths, the
relevant callers/producers/consumers, the observable acceptance condition, and
one or more verification commands with expected exit/output. Keep signatures,
schemas, and short test skeletons inline when they encode a cross-slice
contract. Do not prescribe an algorithm that belongs in `/impl`.

```yaml
slug: <kebab-case>
status: draft | approved
goal: <observable goal>
slices:
  - id: 1
    title: <slice>
    files:
      create: []
      modify: [<exact/path>]
      test: [<exact/path>]
    acceptance: <observable condition>
    verification:
      - command: <shell command>
        expected_exit_code: 0
    public_contracts: []
    decision_needed: false
    options: []
```

The plan is approved only when every changed path has an owner slice, every
acceptance has a proving command, and no placeholder or unresolved WHAT remains.
`public_contracts` and `public_callers` are required when a public symbol or
artifact changes; discover callers with `git grep` rather than guessing.

Before emitting `PLAN_READY`, the planning owner applies the active
`spec-novelist` ownership and timing contract. A controller cannot run that
pre-approval pass on the planning owner's behalf or count its own advisory pass
as satisfying the gate.

## Risk and decisions

Surface user-facing flow choices, irreversible operations, user data,
permissions, database/schema, public contracts, external state, concurrency,
and migrations as explicit decisions. Internal HOW choices remain with the
implementer. Add a spike only for a concrete uncertainty whose failure would be
costly; routine work does not need one.

## Verification and handoff

Use the smallest relevant oracle: unit test, command, fixture comparison,
artifact existence, visual check, or custom command. The implementer runs these
commands and confirms the exact changed paths are within the slice. A checkpoint
or final review is conditional on the risk predicates in `/impl`; the plan does
not require a reviewer or unverifiable transport metadata as a gate.

Before implementation, obtain user approval for any external work or changes to
user data, permissions, database/schema, public contracts, concurrency,
migrations, or other external state. Otherwise proceed once `status: approved`
and the packet is closed.
