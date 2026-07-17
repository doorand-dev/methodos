---
name: impl
description: Execute a truly simple, closed change directly; otherwise let the active Luna/max SDD owner dispatch one fresh Luna implementation owner per slice. Luna/high is the delegated default. The SDD owner dispatches selective checkpoint and final reviewers and routes same-thread scoped repair review.
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
- Otherwise the active `luna-max-sdd-owner` dispatches one fresh custom
  `luna-high-worker` for the declared slice.
  The user-selected executor wins. One-shot work uses a built-in subagent unless
  the nearest project instruction requires another transport.

## Delegated effort

Use `luna-high-worker` with Luna `high` by default. Its agent profile fixes
`gpt-5.6-luna` with `high`; do not
depend on a direct model override being exposed by the spawn transport. Escalate
one slice to `luna-max-worker`, which fixes Luna `max`, only
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

The SDD owner owns task-local transport and mechanical routing. It chooses the
implementation owner immediately before dispatch, checks reported commits,
artifact paths/hashes, reviewer terminal status, ancestry, dirty/index state,
and selects the next route. It never edits production implementation files,
makes an implementation WHY commit, or performs semantic self-review.

After a committed report, the SDD owner makes a fresh read-only
`impl-checkpoint-reviewer(gpt-5.6-sol/medium)` call for a required high-risk
slice. When the assembled candidate requires final review, it makes one
fresh read-only `impl-novelist(gpt-5.6-sol/medium)` call. The SDD owner stores
each raw artifact and records its reviewer thread/session identity for repair.

## Implementation owner packet and lifecycle

The SDD owner sends one self-contained packet with: closed acceptance;
`slice_id`; `owner_role=slice-owner`; `owner_thread_or_session` fixed to the
attempt-1 implementation owner identity; declared write/test/artifact paths;
callers/producers/consumers/failures; commands; provenance when a plan exists;
and the WHY format. A final assembly implementation change is its own declared
slice and does not transfer reviewer dispatch.

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

## SDD-owner review and repair loop

Default to no checkpoint. Require it only for a schema or explicit public contract;
authority, permission, secret, or security; persistent/latest/idempotency/
concurrency; migration or external state; financial execution; or a foundation
consumed by two or more later planned slices. Size and complexity alone never
trigger it. Each gating finding back-links one approved acceptance criterion,
user story, or explicit public invariant.

For an attempt-1 `BROKEN`, the SDD owner sends stable finding IDs, exact repair
scope, and declared affected selectors to the same slice owner. That owner makes
the smallest repair in its declared boundary, runs local checks, creates a WHY
repair commit, and returns a new report. The SDD owner follows up in the same
attempt-1 reviewer thread/session with only finding IDs, repair commit/diff,
and affected caller/producer/consumer/failure selectors. This is attempt 2+
`scoped`; never create a dedicated repair-review profile or routine second full
pass.

If repair changes acceptance/oracle, public contract, authority/data behavior,
or the impact graph, the owner returns `BLOCKED`; the SDD owner requests a new
approved lineage rather than widening scoped review. A user-requested single
review skips attempt 2+ and records the residual risk.

The final full reviewer runs once only after the SDD owner has mechanically
accepted all required slice reports and the assembly candidate. Its BROKEN
findings return to the original owner(s) of the affected slice paths; its scoped
re-review is a follow-up to that final reviewer's original thread/session under
the same packet limits.

## Report and seam acceptance

`impl-worker-report` v1.2 contains the actual owner model/effort, `slice_id`,
`owner_role`, `owner_thread_or_session`, touched paths, commit and parent SHA, real command output,
acceptance criteria, impact selectors, unresolved decisions, and workspace
dirty/index state. `checkpoint` and `final_review` are SDD-owner routing
records: before review they are `NOT_REQUESTED`; after review they contain the
artifact, hash, reviewer thread/session identity, terminal status, reviewed and
final candidate SHA. The owner must never claim to have invoked either reviewer.

For each reported owned commit the SDD owner runs `git show` and
`git diff --name-only <sha>^ <sha>`, checks it is within the declared scope,
and checks the real workspace. For every repair it requires
`owner_thread_or_session` to equal the attempt-1 implementation report; a
different or missing identity is `BLOCKED`. It validates each required artifact and its
actual terminal provenance. For several commits, union individual patches;
never substitute a cumulative range. `approved_plan_revision` is provenance,
not a diff base. A mechanical mismatch routes back to the same owner as
`BLOCKED`; it is not an SDD-owner repair or semantic self-review.

## Completion and prohibitions

Complete only after every owner has a WHY commit and local evidence, every
required SDD-owner-dispatched attempt-1 review is terminal, every BROKEN repair
has either same-thread scoped closure or a new approved lineage, and the
SDD owner's mechanical checks pass. A low-risk no-plan packet closes after its
WHY commit, declared check, real evidence, and clean boundary.

- Do not let an implementation owner spawn or call any checkpoint or final reviewer.
- Do not let an SDD owner edit production implementation or perform semantic review.
- Do not make the root/project orchestrator dispatch task-local reviewers; it
  owns inventory, overlap, ordering, HITL, and integration/merge state only.
- Do not create or use a separate final scoped-review profile.
- Do not infer max from multi-slice, cross-module, file count, or plan presence.
- Do not ask “진행할까요?” between approved routes.
