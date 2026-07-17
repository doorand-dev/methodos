---
name: impl-novelist
description: Run the single fresh final integrated verification gate for an assembled Codex implementation. The Luna/max SDD owner calls it after mechanically accepting implementation-owner reports, local checks, and required high-risk checkpoints. Attempt 1 is one gpt-5.6-sol/medium full pass combining four technical lenses with an actor/user-story narrative overlay; failed-review repair is rechecked only by same-thread scoped follow-up.
---

# Impl Novelist

This is the only automatic full reviewer after assembled Codex implementation.
The SDD owner owns its fresh dispatch, artifact, and repair routing. Each slice
owner owns only its declared implementation, local checks, WHY commits, and
report; it never calls a reviewer. The SDD owner must not repeat this gate
semantically.
It combines four ordered technical lenses with the assembled naive-user
narrative. Do not run a separate final full `impl-verify` before or after it.
Ordinary slices receive local checks only; `impl` owns the narrowly conditional
high-risk slice checkpoint.

## Procedure

1. Locate the approved spec/plan when one exists, or the closed execution
   packet for a low-risk no-plan change. Require the lineage provenance,
   `owned_commit_shas`, candidate ref, declared verification commands,
   full-regression command, checkpoint artifacts/residual risks, and repo. Do
   not invent missing inputs.
2. Read the nearest project machine route at point of use. External ChatGPT Pro
   or Claude Fable/Opus is allowed only when the user explicitly requests it.
3. For attempt 1, the SDD owner dispatches the fresh read-only
   `impl-novelist(gpt-5.6-sol/medium)` profile with `fork_turns="none"` as the
   final quality floor. Send the self-contained packet only after spawning.
4. Pass a self-contained packet: approved or closed requirements, slice or
   execution-packet contracts, `approved_plan_revision` as provenance only,
   the authoritative `owned_commit_shas`, optional `candidate_diff_base` for
   regression context only, the candidate SHA, actual candidate source, impact
   selectors, and commands. Do not pass implementation discussion or prior DONE
   claims.
5. Require `impl-narrative-final` v1.4 JSON. The full reviewer must execute one
   ordered pass: (1) requirements/scope, (2) caller/producer/consumer/failure
   impact, (3) quality/debt, (4) test oracle/regression, then actor/user-story
   narrative overlay. DONE ends the workflow immediately;
   never schedule a routine second review.
6. If attempt 1 or later returns BROKEN, the SDD owner returns each stable
   finding to the original owner of the affected slice paths. Those owners
   implement the smallest repairs, create WHY commits, and return reports. The SDD owner follows up in
   the attempt-1 reviewer's same thread/session for attempt 2+ with only finding
   IDs, repair commit/diff, affected impact/flow/test selectors, and candidate
   ref. Re-run only selected lenses; justify every unaffected lens as `SKIPPED`.
   Never use a separate repair-review profile.
7. If a repair changes approved requirements, acceptance/oracle, public contract,
   authority/data behavior, or the impact graph itself, the owner stops and the
   SDD owner surfaces the required user decision to the root orchestrator and
   starts the approved new lineage after HITL.
   Start a new lineage attempt 1 full only after approval. Never promote
   attempt 2+ to full.
8. If the local subagent cannot run or the context packet is insufficient,
   return `NEEDS_CONTEXT`; do not auto-call an external provider. For an
   explicitly requested external review, apply that provider's session/model/
   finality contract and treat its final `BROKEN`, `NEEDS_CONTEXT`, or
   issue-bearing result as a successful review result. Its failure does not
   authorize another provider automatically.

## Boundaries

- Scope the review from the explicit owned commit set. For every
  `owned_commit_shas` entry, inspect `git show <sha>` and its
  `<sha>^..<sha>` patch, then union those patches. A single owned commit uses
  `commit^..commit`; multiple owned commits must not be replaced by a
  first-owned..last-owned range.
- `approved_plan_revision` identifies the approved lineage/provenance only. It
  is never the code diff base. `candidate_diff_base`, when present, is a
  regression baseline only and is not an ownership boundary.
- Inspect external commits between the provenance revision and candidate only
  for declared-path or declared-contract overlap. Non-overlapping interleaving
  is `PASS` and excluded from scope; overlap is `BLOCKED`. If the owned commit
  set is missing, return `NEEDS_CONTEXT` instead of guessing a range.

- Gate a finding only when it backlinks an exact approved acceptance criterion,
  user story, or explicit public invariant. Without one, classify it as
  non-gating `polish` or `deferred_decision`.
- Require observable behavior, not a preferred implementation. Request the
  minimum test oracle that proves the linked invariant; do not inflate coverage
  for unrelated code or hypothetical paths.
- A high-risk checkpoint does not replace this final integration gate, and this
  gate does not justify a second final full review.
- An SDD-owner seam check does not replace this gate and must not repeat its
  semantic lenses. It only checks commit boundary, ancestry, terminal artifact,
  hashes, and dirty/index state reported by the slice owners and SDD owner.

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for the lightweight spec-stage narrative before planning.
- Do not add another automatic reviewer before or after this final gate.
