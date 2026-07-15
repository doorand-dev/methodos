---
name: impl
description: Implement an approved Codex plan one slice at a time, run each slice's declared local RED/GREEN and verification checks, confirm the diff boundary, and create WHY commits. Trigger when an approved plan has unimplemented slices. Skip reviewer checkpoints by default; dispatch one fresh read-only checkpoint only for an explicitly high-risk slice. After all slices pass, dispatch the single final impl-novelist gate; attempt 1 is full and only failed-review repairs use scoped attempt 2+.
---

# /impl — slices to one final verified candidate

## Trigger and prerequisites

- Trigger when `plan.status=approved` and a planned slice lacks its commit.
- Also trigger on `구현`, `implement`, `이 슬라이스 만들어`, `/impl <slice>`.
- Resolve `plan_root` and `verify_root` from the nearest `AGENTS.md` or project
  convention. Require the approved plan and exact slice contract.
- Do not require a `plan-verify` artifact. Deterministic plan preflight and any
  conditional high-risk `decision-reviewer` must already be closed.
- A direct 1-2-file task with no formal plan follows the normal implementation
  path: minimal edit, at least one relevant check, and project-required commit.
  It does not manufacture Methodos artifacts or subagents.

## Implement each slice

1. Paste the complete slice contract into the implementation context. Stay
   inside declared create/modify/test paths. Stop on intent overrun or a new
   user-visible, authority/data, public-contract, or irreversible decision.
2. Before editing, inspect existing owners and all changed public callers. For
   artifacts and pipelines, close producer → consumer → derived-output paths.
3. Make the minimum implementation. Do not add unrequested abstractions,
   configurability, or out-of-scope cleanup.
4. Run the declared verification command locally. Record actual command, exit,
   and output. For `unit_test`, observe real RED before implementation and GREEN
   after it. For deterministic artifacts, exercise the declared integrated
   selector rather than checking file existence alone.
5. Check actual touched paths with `git diff --name-only`. Resolve unexpected
   paths before committing.
6. Commit the completed slice with only owned paths:

   ```text
   <한 줄 제목>

   WHY: <결정> | 비용(지금/부채): Xm/Ym | Reeval: <조건>
   Slice: <id>
   Touched: <paths>
   ```

7. Classify the completed slice using the checkpoint predicate below. Skip by
   default. When it matches, close the one checkpoint before a downstream slice
   consumes the changed foundation.
8. Continue directly to the next slice after the local contract and any required
   checkpoint are closed. Do not create Claude `slice-<N>-attempt-<M>.json`.

Large independent slices may use an implementation subagent, but its prompt
must include the exact slice, touched paths, impact closure, verification
commands, RED/GREEN requirement, and WHY commit format. Implementation
delegation is not a verification gate.

## High-risk slice checkpoint

Default to `SKIP`. Require a checkpoint only when the slice changes at least one
of these observable risk surfaces:

- schema or explicit public contract;
- approval, authority, permission, secret, or security behavior;
- persistent artifact, latest pointer, idempotency, or concurrency behavior;
- migration or external state;
- order, capital allocation, or financial-execution semantics;
- a foundation consumed by two or more later planned slices.

For each matching slice:

1. After its WHY commit and local checks, dispatch the fresh read-only
   `impl-checkpoint-reviewer(gpt-5.6-sol/medium)` with `fork_turns="none"`.
   Send only the approved slice contract, base/candidate refs, actual diff,
   risk trigger, affected caller/producer/consumer/failure selectors, and
   declared commands. Store attempt 1 at
   `<verify_root>/checkpoint-<slug>-slice-<N>-attempt-1.json`.
2. Run exactly one full attempt 1 for that slice and approved-plan revision.
   Never schedule a routine second full checkpoint.
3. On `BROKEN`, repair the stable findings with a WHY commit. Unless the user
   explicitly limited this task to one review, dispatch the same profile fresh
   for attempt 2+ scoped to stable issue IDs, repair paths, affected selectors,
   and targeted commands. Do not repeat the baseline full review.
4. When the user said `검토 1회만` or an equivalent limit, skip checkpoint
   re-review after repair. Pass the prior findings, repair diff, unrerun
   selectors, and residual risk into the final integrated gate; never describe
   the checkpoint as independently closed.
5. If repair changes an approved acceptance/oracle, public contract,
   authority/data behavior, or the impact graph, stop scoped routing. Close the
   required decision and plan revision, then start a new checkpoint lineage in
   which that revised slice may receive one full attempt 1.

Every gating checkpoint finding must backlink one exact approved acceptance
criterion, user story, or explicit public invariant. Without that backlink it
is non-gating polish/deferred work. A reviewer may require an observable
invariant and its minimum proving oracle, but never a particular implementation.

## Final candidate gate

After every planned slice is committed and local checks pass:

1. Identify the approved plan revision, regression base, final candidate SHA,
   full spec/plan requirements, actual diff, impact graph, declared targeted
   commands, one full-regression command when the project declares one, and all
   high-risk checkpoint results or explicit one-review-only residual risks.
2. Dispatch fresh read-only `impl-novelist(gpt-5.6-sol/medium)` attempt 1 full
   with `fork_turns="none"` as the final quality floor. Pass the review packet
   after spawning; never inherit all or recent main-session turns.
3. The final reviewer independently runs the four technical lenses in order:
   requirements/scope; caller/producer/consumer/failure impact; quality/debt;
   test oracle/full regression. It then overlays every actor/user story.
4. `DONE` ends the workflow. Never schedule a routine second review.
5. `BROKEN` returns stable issues to this skill. Make the smallest repair and a
   WHY commit, then dispatch with `fork_turns="none"` the fresh
   parent-model/effort `impl-novelist-scoped-reviewer` as attempt 2+ with only:
   prior issue closure, repair paths, affected impact/flow/test selectors, and
   the new candidate SHA.
6. If a repair changes approved requirements, acceptance/oracle, public
   contract, authority/data behavior, or the impact graph itself, obtain any
   required user decision and start a new lineage attempt 1 full. Do not widen
   attempt 2+ into full.
7. If the reviewer or packet is unavailable, return `NEEDS_CONTEXT`. Do not
   replace it with controller self-review or an automatic external provider.

ChatGPT Pro or Claude Fable/Opus is allowed only when the user explicitly asks
for that external review. Its failure never authorizes another provider.

## Completion evidence

Goal completion requires:

- all planned WHY commits;
- actual local command outputs for every slice;
- every matched high-risk slice has one full checkpoint artifact, while ordinary
  slices have none; one-review-only repairs carry explicit residual risk forward;
- latest `<verify_root>/narrative-<slug>-final-attempt-<M>.json` status `DONE`;
- final attempt 1 artifact has every stage PASS, or the latest scoped repair
  artifact has selected stages PASS and justified unaffected stages SKIPPED;
- final artifact `terminal_regression` containing the actual command/output or
  `NOT_DECLARED` with residual scope.

## Do not

- wait for or create Codex `plan-verify`/routine per-slice `impl-verify` artifacts;
- broaden the checkpoint predicate because a slice is merely large or complex;
- treat implementer reports or commit messages as final evidence;
- modify files outside a slice without updating the approved contract;
- claim an unrun command, caller, consumer, or user flow was verified;
- ask "진행할까요?" between approved slices.
