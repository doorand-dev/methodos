---
name: impl
description: Implement an approved Codex plan one slice at a time, run each slice's declared local checks, close caller and data-flow impact, and create WHY commits. Trigger when an approved plan has unimplemented slices. Do not wait for plan-verify and do not dispatch per-slice impl-verify. After all slices pass local checks, dispatch the single final impl-novelist verification gate; attempt 1 is full and only failed-review repairs use scoped attempt 2+.
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

7. Continue directly to the next slice. Do not dispatch a fresh reviewer or
   create `slice-<N>-attempt-<M>.json` between slices.

Large independent slices may use an implementation subagent, but its prompt
must include the exact slice, touched paths, impact closure, verification
commands, RED/GREEN requirement, and WHY commit format. Implementation
delegation is not a verification gate.

## Final candidate gate

After every planned slice is committed and local checks pass:

1. Identify the approved plan revision, regression base, final candidate SHA,
   full spec/plan requirements, actual diff, impact graph, declared targeted
   commands, and one full-regression command when the project declares one.
2. Dispatch fresh read-only `impl-novelist` attempt 1 full. Its profile omits
   `model` and `model_reasoning_effort`, so it inherits the parent session.
3. The final reviewer independently checks requirements/scope, caller and data
   impact, code quality, commands/full regression, and every actor/user story.
4. `DONE` ends the workflow. Never schedule a routine second review.
5. `BROKEN` returns stable issues to this skill. Make the smallest repair and a
   WHY commit, then dispatch fresh
   `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)` as attempt 2+ with only:
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
- latest `<verify_root>/narrative-<slug>-final-attempt-<M>.json` status `DONE`;
- final attempt 1 artifact has every stage PASS, or the latest scoped repair
  artifact has selected stages PASS and justified unaffected stages SKIPPED;
- final artifact `terminal_regression` containing the actual command/output or
  `NOT_DECLARED` with residual scope.

## Do not

- wait for or create Codex `plan-verify`/per-slice `impl-verify` artifacts;
- treat implementer reports or commit messages as final evidence;
- modify files outside a slice without updating the approved contract;
- claim an unrun command, caller, consumer, or user flow was verified;
- ask "진행할까요?" between approved slices.
