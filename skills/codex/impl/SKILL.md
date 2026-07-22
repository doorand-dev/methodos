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

File count is not a routing cutoff. A coherent multi-file packet is still
direct when the goal, paths, and checks are closed. Run the command, inspect
the exact changed paths, and commit according to repository rules.

## Delegated execution

Before choosing implementation topology, apply `/plan`'s Trigger. If it
matches, stop before implementation and obtain an approved plan; delegation
never substitutes for SDD approval.

Once the work is in `/impl`, delegate exactly one declared closed
implementation slice to `luna-high-worker` by default. This model default
applies to a slice executor, whether it is an independent implementation-only
thread or a subagent/worker. It does not select the model for a task that owns
planning, diagnosis, integration, or a multi-slice lifecycle. An existing
owning task may direct-execute one closed low-risk packet in its current session
without changing its session model.

After decomposition, use `luna-max-worker` only when that slice
retains a concrete high-cost, hard-to-recover uncertainty in cause, impact, or
verification, or Luna/high has failed to converge. Multi-slice work, file
count, cross-module reach, and a plan alone are not max reasons.

The worker owns only its declared paths: inspect callers and failure paths,
edit, run the declared tests/commands, verify the changed-path boundary, and
report the result. It does not decide whether a review is needed and does not
claim execution facts that the runtime did not expose.

### Supervised wait

After spawning a supervised built-in subagent whose result gates the next
step, call `wait_agent` once with the longest supported timeout. It returns
immediately on terminal status; if the wrapper yields, resume the same wait
instead of polling status or transcript. A timeout is not worker failure;
re-wait only if the result is still needed. After wake, verify the declared
evidence before claiming completion.

## Optional review

Do not review by default. Request a targeted checkpoint when the slice changes
an explicit public contract, permission/security or user data, persistent/latest
or idempotency/concurrency behavior, migration or external state, financial
execution, or a foundation shared by multiple independent slices. The review
runs on the `impl-checkpoint-reviewer` agent (read-only) with the relevant
command and exact-path check; every blocking finding points
to an approved acceptance condition or invariant.

Request a final review on the `impl-novelist` agent (read-only) only when the
candidate introduces a new public or user
flow, changes a shared contract or permission/data boundary, touches external
state/concurrency/migration, or combines multiple independent slices with a
real integration omission risk. Otherwise local verification is sufficient.

For a broken targeted review, send stable finding IDs and the smallest repair
scope to the original owner, then recheck only the affected selectors and
commands. If acceptance, public contract, authority/data behavior, or the
impact graph changes, stop and obtain a new approved plan.

## Completion

Completion requires the declared tests/commands to pass and the exact changed
paths to remain within scope. External work, user data, permissions, database
or schema changes, public contracts, concurrency, migrations, and other
external-state effects require the applicable user approval before completion.

Do not make an implementation owner spawn reviewers. Do not turn transport
metadata, generated artifacts, or commit prose into a completion gate.
