---
name: impl-novelist
description: Run the single fresh final verification gate for an assembled Codex implementation. Self-trigger after all planned implementation commits and local checks are complete, or on explicit final implementation review / impl novelist requests. Attempt 1 is full and inherits the parent model and effort; only repairs after a failed final review use scoped gpt-5.6-sol/medium. Do not run a routine second round after DONE.
---

# Impl Novelist

This is the only automatic fresh reviewer after Codex implementation. It combines
technical conformance, impact and quality checks, independent commands, full
regression, and the assembled naive-user narrative. Per-plan `plan-verify` and
per-slice `impl-verify` are not Codex gates.

## Procedure

1. Locate the approved spec/plan, base and candidate refs, declared verification
   commands, full-regression command, and repo. Do not invent missing inputs.
2. Read the nearest project machine route at point of use. External ChatGPT Pro
   or Claude Fable/Opus is allowed only when the user explicitly requests it.
3. For attempt 1, dispatch the fresh read-only `impl-novelist` profile. It omits
   `model` and `model_reasoning_effort`, so both inherit from the parent session.
4. Pass a self-contained packet: approved requirements, slice contracts, exact
   base/candidate refs, actual diff/source, impact selectors, and commands. Do
   not pass implementation discussion or prior DONE claims.
5. Require `impl-narrative-final` v1.3 JSON. DONE ends the workflow immediately;
   never schedule a routine second review.
6. If attempt 1 or later returns BROKEN, implement the repair and dispatch
   `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)` for attempt 2+. Give it
   only stable issue closure, repair paths, affected impact/flow/test selectors,
   and the new candidate ref.
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

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for the lightweight spec-stage narrative before planning.
- Do not add another automatic reviewer before or after this final gate.
