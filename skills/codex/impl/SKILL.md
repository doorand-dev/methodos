---
name: impl
description: Execute a truly simple, closed change directly; otherwise give each declared slice to one fresh Luna implementation owner. Luna/high is the delegated default. The controller, never an implementation owner, dispatches the selective checkpoint and final reviewer and routes same-thread scoped repair review.
---

# /impl — one slice, one implementation owner

## Trigger and route

- Trigger for an approved plan slice or a closed execution packet. A packet has
  one goal, observable acceptance, exact write/test/artifact paths, a command,
  and stop conditions.
- A parent directly performs the minimum edit only when the goal/check are
  closed, the surface is one or two declared files, it has no new user-facing
  WHAT, schema/public API, authority/data/security, irreversible, deployment,
  migration, or external-state effect, and no unexplained dirty overlap.
- Otherwise dispatch one fresh built-in `impl-worker` for the declared slice.
  The user-selected executor wins. One-shot work uses a built-in subagent unless
  the nearest project instruction requires another transport.

## Delegated effort

Use `gpt-5.6-luna` with `high` by default. Escalate one slice to `max` only
when, after decomposition, that slice retains high-cost and hard-to-recover
uncertainty in cause, impact, or verification, or comparable Luna/high work has
demonstrably failed to converge. Multi-slice work, cross-module reach, file
count, or the existence of a plan is not a max condition. Do not make `medium`
the default without comparative evidence.

## Ownership boundary

The implementation owner owns exactly one slice: declared-path implementation,
RED/GREEN and local verification, its WHY commit, and an `impl-worker-report`.
It makes no reviewer call. It stops with `BLOCKED` if the packet lacks a
decision or editing would exceed the declared boundary.

The controller owns transport and mechanical routing only. It chooses the
implementation owner immediately before dispatch, checks reported commits,
artifact paths/hashes, reviewer terminal status, ancestry, dirty/index state,
and selects the next route. It never edits implementation files, makes a WHY
commit, or repeats semantic review.

After a committed report, the controller itself makes a fresh read-only
`impl-checkpoint-reviewer(gpt-5.6-sol/medium)` call for a required high-risk
slice. When the assembled candidate requires final review, it itself makes one
fresh read-only `impl-novelist(gpt-5.6-sol/medium)` call. The controller stores
each raw artifact and records its reviewer thread/session identity for repair.

## Implementation owner packet and lifecycle

The controller sends one self-contained packet with: closed acceptance;
`slice_id`; `owner_role=slice-owner`; `owner_thread_or_session` fixed to the
attempt-1 implementation owner identity; declared write/test/artifact paths;
callers/producers/consumers/failures; commands; provenance when a plan exists;
and the WHY format. It may declare `assembly_owner=true` only for a final
assembly implementation task, but that does not transfer reviewer dispatch.

The owner must:

1. Read relevant declared callers, producers, consumers, derived outputs, and
   failure paths.
2. Implement only declared paths, run declared RED/GREEN and local commands,
   and create one WHY commit before reporting.
3. Return only raw `impl-worker-report`; it must report no checkpoint/final
   reviewer as owner-run. The report is a seam handoff, not semantic approval.

```text
<one-line title>

WHY: <decision> | 비용(지금/부채): Xm/Ym | Reeval: <condition>
Slice: <id>
Touched: <paths>
```

## Controller review and repair loop

Default to no checkpoint. Require it only for a schema or explicit public contract;
authority, permission, secret, or security; persistent/latest/idempotency/
concurrency; migration or external state; financial execution; or a foundation
consumed by two or more later planned slices. Size and complexity alone never
trigger it. Each gating finding back-links one approved acceptance criterion,
user story, or explicit public invariant.

For an attempt-1 `BROKEN`, the controller sends stable finding IDs, exact repair
scope, and declared affected selectors to the same slice owner. That owner makes
the smallest repair in its declared boundary, runs local checks, creates a WHY
repair commit, and returns a new report. The controller follows up in the same
attempt-1 reviewer thread/session with only finding IDs, repair commit/diff,
and affected caller/producer/consumer/failure selectors. This is attempt 2+
`scoped`; never create a dedicated repair-review profile or routine second full
pass.

If repair changes acceptance/oracle, public contract, authority/data behavior,
or the impact graph, the owner returns `BLOCKED`; the controller requests a new
approved lineage rather than widening scoped review. A user-requested single
review skips attempt 2+ and records the residual risk.

The final full reviewer runs once only after the controller has mechanically
accepted all required slice reports and the assembly candidate. Its BROKEN
repair belongs to the same assembly owner; its scoped re-review is a follow-up
to that final reviewer's original thread/session under the same packet limits.

## Report and seam acceptance

`impl-worker-report` v1.2 contains the actual owner model/effort, `slice_id`,
`owner_role`, `owner_thread_or_session`, touched paths, commit and parent SHA, real command output,
acceptance criteria, impact selectors, unresolved decisions, and workspace
dirty/index state. `checkpoint` and `final_review` are controller-owned routing
records: before review they are `NOT_REQUESTED`; after review they contain the
artifact, hash, reviewer thread/session identity, terminal status, reviewed and
final candidate SHA. The owner must never claim to have invoked either reviewer.

For each reported owned commit the controller runs `git show` and
`git diff --name-only <sha>^ <sha>`, checks it is within the declared scope,
and checks the real workspace. For every repair it requires
`owner_thread_or_session` to equal the attempt-1 implementation report; a
different or missing identity is `BLOCKED`. It validates each required artifact and its
actual terminal provenance. For several commits, union individual patches;
never substitute a cumulative range. `approved_plan_revision` is provenance,
not a diff base. A mechanical mismatch routes back to the same owner as
`BLOCKED`; it is not a controller repair or semantic re-review.

## Completion and prohibitions

Complete only after every owner has a WHY commit and local evidence, every
required controller-owned attempt-1 review is terminal, every BROKEN repair
has either same-thread scoped closure or a new approved lineage, and the
controller's mechanical checks pass. A low-risk no-plan packet closes after its
WHY commit, declared check, real evidence, and clean boundary.

- Do not let an implementation owner spawn or call any checkpoint or final reviewer.
- Do not let a controller edit implementation or perform semantic review.
- Do not create or use a separate final scoped-review profile.
- Do not infer max from multi-slice, cross-module, file count, or plan presence.
- Do not ask “진행할까요?” between approved routes.
