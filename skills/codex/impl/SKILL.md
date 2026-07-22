---
name: impl
description: Execute one closed low-risk packet directly; apply the plan trigger before implementation, then delegate one closed implementation slice to Luna/high by default.
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

In `/impl`, delegate exactly one declared closed slice to `luna-high-worker`.
This default applies to a slice executor, not a planning, diagnosis,
integration, or multi-slice owner. An existing owner may direct-execute one
closed low-risk packet without changing its session model.

Use `luna-max-worker` only for a concrete costly-to-recover uncertainty left in
the slice or after Luna/high fails to converge. Size, reach, and a plan alone
do not justify max.

The worker inspects relevant callers and failure paths, edits only declared
paths, runs declared checks, and reports the result. It neither chooses review
nor claims unobserved execution facts.

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
