---
name: impl
description: Execute one closed low-risk packet directly; apply the plan trigger, then choose Luna/high or Luna/max for one closed implementation slice.
---

# /impl — implementation routing

## Closed execution packet

Use direct execution when one packet closes all of these:

- one observable goal and acceptance condition;
- exact write paths (any number of files), relevant callers/producers/consumers,
  and a verification command with a clear pass condition;
- no unresolved user-facing choice, new schema/public contract, permission or
  user-data change, irreversible migration, concurrency change, or external
  state side effect;
- no unexplained overlap with existing dirty changes.

## Delegated execution

Before choosing implementation topology, apply `/plan`'s Trigger. If it
matches, stop before implementation and obtain an approved plan; delegation
never substitutes for SDD approval.

Root controllers do not enter `/impl`; the global role gate routes them to the
active `root-controller` contract. "Existing owner" below means a lifecycle or
one-slice implementation owner, never a root controller.

In `/impl`, choose one worker for exactly one declared closed slice:

- `luna-high-worker` when implementation and verification are routine;
- `luna-max-worker` before spawn when a concrete costly-to-recover uncertainty
  remains, including cross-restart state, concurrency/CAS, or exactly-once
  behavior. Use max also after Luna/high fails to converge.

This choice applies to a slice executor, not a planning, diagnosis,
integration, or multi-slice owner. An existing owner may direct-execute one
closed low-risk packet without changing its session model. Size, reach, and a
plan alone do not justify max.

A multi-slice lifecycle lead remains the lead and spawns each declared closed
slice as a built-in implementation worker. Same-thread conversion to a Luna
executor follows the global independent-session contract and is only for a true
one-slice lifecycle with no remaining child, HITL, checkpoint, repair, or
planning work; it never converts back to a planning lead in that lifecycle.

A declared slice may be composite: keep small sequential substeps in one worker
when they share the same goal, acceptance, ownership, risk, verification,
approval, and rollback boundary. Reuse an existing worker or owner only to
complete, correct, or re-verify that same open slice. Do not append a new goal,
acceptance, write scope, or risk boundary; that requires a new slice and fresh
routing.

The worker inspects relevant callers and failure paths, edits only declared
paths, runs declared checks, and reports the result. It neither chooses review
nor claims unobserved execution facts. A new WHAT or expanded lifecycle returns
`BLOCKED|NEEDS_USER` to the owning lead or parent instead of turning the worker
into a planner.

### Verification budget

The declared focused verification commands are the slice worker's ceiling. The
worker does not broaden a selector to a whole test file or suite and does not
add a full regression. Diagnostic commands may locate the defect, but they do
not become extra completion gates. If the declared oracle cannot prove the
changed behavior, return that gap to the owning lead for a plan update instead
of silently expanding verification.

Run a full regression only when an explicit review risk predicate requires it.
The multi-slice lifecycle lead or integration owner assigns it once, after the
assembled candidate and planned repairs are complete. Downstream owners reuse
that result while the reviewed candidate and assumptions remain unchanged; they
do not repeat it at each boundary.

### Supervised wait

After spawning a supervised built-in subagent whose result gates the next
step, call `wait_agent` once with the longest supported timeout. It returns
immediately on terminal status; if the wrapper yields, resume the same wait
instead of polling status or transcript. A timeout is not worker failure;
re-wait only if the result is still needed. After wake, verify the declared
evidence before claiming completion.

## Optional review

Do not review by default. Use `impl-checkpoint-reviewer` only for explicit
public-contract, permission/security/user-data, persistent/idempotency/
concurrency, migration/external-state, financial, or shared-foundation changes.
Each blocking finding cites an approved acceptance condition or invariant.

Review ownership follows the lifecycle boundary. At a planned checkpoint inside
an approved multi-slice plan, the planning/integration lead spawns the fresh,
read-only `impl-checkpoint-reviewer` as its child. That lead owns findings back
to the affected slice worker, repair, affected-finding re-review, and release of
the next slice. A one-slice implementation worker never chooses, spawns, or
performs its own review. The lead may perform a routine local checkpoint only
when the named reviewer predicate above does not match.

A root-owned integration/HITL review is outside this skill and follows the
`root-controller` contract plus the reviewer profile. A prior lead-owned PASS
satisfies the internal checkpoint while its reviewed candidate and assumptions
remain unchanged.

Use `impl-novelist` only for a new public/user flow, shared contract or
authority/data boundary, external-state/concurrency/migration change, or a real
integration omission risk across independent slices. Otherwise local
verification is sufficient.

Return stable findings to the original owner and recheck only affected
commands. If acceptance, contract, authority/data behavior, or the impact graph
changes, stop and obtain a new approved plan.

## Completion

Completion requires declared checks to pass, changed paths to remain in scope,
and every user approval required by `/plan` to be present.
