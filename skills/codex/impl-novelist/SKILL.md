---
name: impl-novelist
description: Run the single fresh final integrated verification gate for an assembled Codex implementation. Self-trigger after all planned commits, local checks, and required high-risk slice checkpoints are complete, or on explicit final implementation review / impl novelist requests. Attempt 1 is one gpt-5.6-sol/medium full pass combining four technical lenses with an actor/user-story narrative overlay; only failed-review repairs use scoped re-review. Never pair it with another final full impl-verify or run a routine second round after DONE.
---

# Impl Novelist

This is the only automatic full reviewer after assembled Codex implementation.
It combines four ordered technical lenses with the assembled naive-user
narrative. Do not run a separate final full `impl-verify` before or after it.
Ordinary slices receive local checks only; `impl` owns the narrowly conditional
high-risk slice checkpoint.

## Procedure

1. Locate the approved spec/plan, base and candidate refs, declared verification
   commands, full-regression command, checkpoint artifacts/residual risks, and
   repo. Do not invent missing inputs.
2. Read the nearest project machine route at point of use. External ChatGPT Pro
   or Claude Fable/Opus is allowed only when the user explicitly requests it.
3. For attempt 1, dispatch the fresh read-only
   `impl-novelist(gpt-5.6-sol/medium)` profile with `fork_turns="none"` as the
   final quality floor. Send the self-contained packet only after spawning.
4. Pass a self-contained packet: approved requirements, slice contracts, exact
   base/candidate refs, actual diff/source, impact selectors, and commands. Do
   not pass implementation discussion or prior DONE claims.
5. Require `impl-narrative-final` v1.4 JSON. The full reviewer must execute one
   ordered pass: (1) requirements/scope, (2) caller/producer/consumer/failure
   impact, (3) quality/debt, (4) test oracle/regression, then actor/user-story
   narrative overlay. DONE ends the workflow immediately;
   never schedule a routine second review.
6. If attempt 1 or later returns BROKEN, implement the repair and dispatch the
   parent-model/effort `impl-novelist-scoped-reviewer` with `fork_turns="none"`
   for attempt 2+. Give it
   only stable issue closure, repair paths, affected impact/flow/test selectors,
   and the new candidate ref. Re-run only selected lenses; justify every
   unaffected lens as `SKIPPED`.
7. If a repair changes approved requirements, acceptance/oracle, public contract,
   authority/data behavior, or the impact graph itself, obtain any required user
   decision and start a new lineage attempt 1 full. Never promote attempt 2+ to full.
8. If the local subagent cannot run or the context packet is insufficient,
   return `NEEDS_CONTEXT`; do not auto-call an external provider. For an
   explicitly requested external review, apply that provider's session/model/
   finality contract and treat its final `BROKEN`, `NEEDS_CONTEXT`, or
   issue-bearing result as a successful review result. Its failure does not
   authorize another provider automatically.

## Boundaries

- Gate a finding only when it backlinks an exact approved acceptance criterion,
  user story, or explicit public invariant. Without one, classify it as
  non-gating `polish` or `deferred_decision`.
- Require observable behavior, not a preferred implementation. Request the
  minimum test oracle that proves the linked invariant; do not inflate coverage
  for unrelated code or hypothetical paths.
- A high-risk checkpoint does not replace this final integration gate, and this
  gate does not justify a second final full review.

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for the lightweight spec-stage narrative before planning.
- Do not add another automatic reviewer before or after this final gate.
