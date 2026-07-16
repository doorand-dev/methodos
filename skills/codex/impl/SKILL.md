---
name: impl
description: Route every implementation write, including a direct 1-2-file task, through a fresh gpt-5.6-luna/max impl-worker. The worker owns implementation, local verification, WHY commits, selective high-risk checkpoints, and—when it is the assembly owner—the single final impl-novelist gate with repair. The planning/orchestration session owns WHAT, slice boundaries, model route, and candidate ancestry; the upper controller performs seam checks only.
---

# /impl — worker-owned implementation to one final verified candidate

## Trigger and prerequisites

- Trigger when `plan.status=approved` and a planned slice lacks its commit.
- Also trigger on `구현`, `implement`, `이 슬라이스 만들어`, `/impl <slice>`.
- Resolve `plan_root` and `verify_root` from the nearest `AGENTS.md` or project
  convention. Require the approved plan and exact slice contract.
- Do not require a `plan-verify` artifact. Deterministic plan preflight and any
  conditional high-risk `decision-reviewer` must already be closed.
- A direct 1-2-file task with no formal plan follows the same worker write path:
  dispatch a fresh `impl-worker`, run its declared check, and perform parent
  seam acceptance. It does not manufacture Methodos review artifacts unless the
  packet marks `final_review_required=true`.

## Ownership contract

The planning/orchestration session owns only the decision surface needed to route
the work:

- WHAT, approved acceptance criteria, and user-facing scope;
- slice boundaries and exact write/test/artifact paths;
- model route (`impl-worker` = `gpt-5.6-luna`/`max`);
- the base ref, prior worker commit ancestry, and who is the assembly owner.

It does not edit implementation files, create WHY commits, perform semantic
review, or dispatch the final reviewer on the worker's behalf.

The fresh `impl-worker` owns the implementation lifecycle in the target checkout:

1. implement only the declared slice or assembly task;
2. run declared local verification;
3. create the WHY commit with only declared implementation and evidence paths;
4. when the slice is high-risk, call the fixed Sol/medium checkpoint, repair
   stable findings, and run only the scoped reverify required by that checkpoint;
5. when marked `assembly_owner=true` and `final_review_required=true`, call the
   fresh final `impl-novelist`, repair stable findings, and run only scoped final
   reverify; and
6. return a raw `impl-worker-report` containing commit, reviewer, artifact, and
   ancestry evidence.

If one worker performs the whole implementation, that worker is the assembly
owner. If several workers contribute, the worker that merges or assembles their
results is the only assembly owner and the only worker that calls the final full
`impl-novelist` for that candidate. There is exactly one final full attempt for
the approved lineage.

The upper Sol/controller owns mechanical seam acceptance only. It verifies the
reported commit boundary, ancestry, reviewer terminal status, artifact paths and
hashes, dirty/index state, and the next routing decision. It must not repeat the
worker's requirements, impact, quality, or narrative review and must not repair
implementation files itself. A seam mismatch routes back to the worker as
`BLOCKED`.

## Implementation worker boundary

Every implementation write, including a direct 1-2-file implementation, MUST be
performed by an independent `impl-worker` thread. The profile is fixed to
`gpt-5.6-luna`/`max`; the session's live permission mode still governs whether
the thread can write and commit.

The parent sends one self-contained packet containing:

- the approved WHAT and acceptance criteria;
- the exact slice or assembly boundary;
- `base_ref`, prior candidate/worker commit SHAs, and the required ancestry;
- `write_paths`, `test_paths`, and `artifact_paths`;
- caller/producer/consumer/failure selectors;
- declared local and reviewer commands;
- `assembly_owner` and `final_review_required` flags; and
- the WHY commit format and stop conditions.

The worker may modify and commit only those declared paths. It must not make a
new user-facing, authority/data, public-contract, or irreversible decision. It
must stop with `BLOCKED` and return the decision gap when the packet is
insufficient.

The worker's report is a handoff for mechanical seam acceptance, not a license
for the parent to repeat semantic review. The parent checks the real commit and
workspace state against this report before routing the next slice.

## Worker report

The worker returns ONLY raw JSON. The report must include the actual model and
effort, commit ancestry, touched paths, fresh command output, and the terminal
state of every reviewer it owned:

```json
{
  "schema_version": "1.1",
  "kind": "impl-worker-report",
  "status": "IMPLEMENTED" | "BLOCKED",
  "owner_role": "slice-owner" | "assembly-owner",
  "slice_id": "...",
  "touched_paths": ["..."],
  "commit_sha": "..." | null,
  "parent_sha": "..." | null,
  "checks": [{"command": "...", "exit_code": 0, "output": "..."}],
  "checkpoint": {
    "required": false,
    "status": "SKIPPED",
    "artifact_path": null,
    "artifact_sha256": null,
    "reviewed_candidate_sha": null,
    "final_candidate_sha": null,
    "reviewer_model": null,
    "reviewer_reasoning_effort": null,
    "reviewer_transport": null
  },
  "final_review": {
    "required": false,
    "status": "SKIPPED",
    "artifact_path": null,
    "artifact_sha256": null,
    "reviewed_candidate_sha": null,
    "final_candidate_sha": null,
    "reviewer_model": null,
    "reviewer_reasoning_effort": null,
    "reviewer_transport": null
  },
  "acceptance_criteria": ["..."],
  "impact": {"callers": ["..."], "producers": ["..."], "consumers": ["..."], "failures": ["..."]},
  "unresolved": [],
  "workspace": {"dirty_paths": [], "staged_paths": []},
  "worker_model": "gpt-5.6-luna",
  "worker_reasoning_effort": "max"
}
```

`checkpoint` and `final_review` must record the actual artifact path, reviewer
status, reviewed candidate SHA, and final candidate SHA when required. A
`BLOCKED` report may leave the commit and reviewer fields null, but it must
state the exact missing decision, failed command, or scope mismatch.

## Worker lifecycle

1. Read the approved packet, existing owners, and the relevant caller,
   producer, consumer, derived-output, and failure paths.
2. Edit only the declared implementation paths and run every declared local
   RED/GREEN and verification command.
3. Create the implementation WHY commit before any optional reviewer:

   ```text
   <한 줄 제목>

   WHY: <결정> | 비용(지금/부채): Xm/Ym | Reeval: <조건>
   Slice: <id>
   Touched: <paths>
   ```

   An assembly owner uses `Role: assembly-owner` and lists the input worker
   commits in the body. Evidence artifacts use the same WHY format when they
   require a separate commit.
4. Apply the high-risk checkpoint predicate below. For a matching slice, spawn
   a fresh read-only `impl-checkpoint-reviewer(gpt-5.6-sol/medium)` with
   `fork_turns="none"`, persist its raw JSON at the declared artifact path, and
   close attempt 1 before routing downstream work. On `BROKEN`, the worker
   repairs only stable findings, creates a WHY repair commit, and runs the same
   profile scoped to those findings. Never schedule a routine second full pass.
   If the repair changes acceptance/oracle, a public contract, authority/data
   behavior, or the impact graph, stop with `BLOCKED` for a new plan lineage.
5. When the packet marks the worker as assembly owner and final review required,
   wait until all declared worker inputs and local checks are assembled. Spawn a
   fresh read-only `impl-novelist(gpt-5.6-sol/medium)` with
   `fork_turns="none"`, persist the raw v1.4 artifact, and close the one full
   final attempt. On `BROKEN`, repair only stable findings in the worker-owned
   checkout, create a WHY repair commit, then spawn the fresh
   `impl-novelist-scoped-reviewer` for attempt 2+ with only the repair scope.
   Do not run another full final review. If the repair changes approved
   requirements, acceptance/oracle, public contract, authority/data behavior,
   or the impact graph, stop with `BLOCKED` and request a new approved lineage.
6. Return the raw report only after the final worker-owned commit, reviewer
   artifact, and workspace state are observable.

## Upper controller seam acceptance

After receiving the worker report, the planning/orchestration session performs
only these checks:

1. `git show --format=fuller --stat <commit_sha>` confirms the commit exists,
   has the expected parent, and contains the required WHY line.
2. `git diff --name-only <parent_sha> <commit_sha>` is a subset of the declared
   implementation/evidence paths; no unexpected path is accepted.
3. `git status --short`, `git diff --name-only`, and
   `git diff --cached --name-only` show no worker residue beyond explicitly
   declared next-stage artifacts. The controller does not stage or clean it.
4. Every required checkpoint/final artifact exists, parses, has the expected
   terminal status, records actual reviewer model/effort/transport, and has the
   expected hash when the packet declares one.
5. `candidate_sha`, `parent_candidate_sha`, worker commit SHAs, and the approved
   plan revision form the required ancestry. Only then route the next slice or
   declare the candidate ready.

Do not reopen semantic review from these checks. If any mechanical check fails,
route the exact mismatch back to the owning worker and keep the candidate
closed.

## High-risk slice checkpoint predicate

Default to `SKIP`. Require a checkpoint only when the slice changes at least one
of these observable risk surfaces:

- schema or explicit public contract;
- approval, authority, permission, secret, or security behavior;
- persistent artifact, latest pointer, idempotency, or concurrency behavior;
- migration or external state;
- order, capital allocation, or financial-execution semantics; or
- a foundation consumed by two or more later planned slices.

Size or complexity alone never triggers it. Every gating finding must backlink
one exact approved acceptance criterion, user story, or explicit public
invariant. Without that backlink it is non-gating `polish` or
`deferred_decision`.

## Final candidate completion

The worker-owned candidate is complete only when:

- every planned worker slice has its WHY commit;
- every required checkpoint has one full attempt 1 artifact, with only stable
  repair reverify artifacts after a failure;
- the assembly owner has one final `impl-novelist` attempt 1 artifact with
  status `DONE`, all stages PASS, and actual terminal regression output or
  `NOT_DECLARED` residual scope; and
- the upper controller's mechanical seam checks pass.

`DONE` ends the workflow. Never create a routine second final full review.

## Do not

- let the parent write implementation files or create WHY commits;
- let the parent perform semantic implementation review after worker review;
- let a non-assembly worker call the final full reviewer;
- wait for or create Codex `plan-verify`/routine per-slice `impl-verify` artifacts;
- broaden the checkpoint predicate because a slice is merely large or complex;
- treat a worker report as a substitute for checking the real commit, artifact,
  ancestry, or dirty/index state;
- modify files outside the worker packet; or
- ask “진행할까요?” between approved slices.
