---
name: plan
description: Decompose an approved spec or multi-slice non-trivial Codex task into executable slices, exact files, contracts, decisions, verification commands, and selective high-risk checkpoint annotations. Self-trigger after spec approval or before multi-slice implementation. Skip formal planning for a clear 1-2-file task with no user-visible flow, schema/public API, authority/data, irreversible change, or unresolved WHAT decision. After approval, run deterministic preflight and one conditional decision review, then implement with local checks, checkpoint only explicit high-risk slices, and finish with one integrated impl-novelist gate.
---

# /plan — approved intent를 executable slices로 변환

## Trigger and direct path

- Trigger after an approved spec or before multi-slice non-trivial implementation.
- Explicit triggers: `plan`, `계획 짜`, `PRD 작성`, `기능 분해`, `/plan <slug>`.
- After a read-only impact scan, skip this skill when the goal/check are clear,
  only 1-2 files are expected, and there is no user-visible flow, schema/public
  API, security/authority/data/user-asset, irreversible, or unresolved WHAT
  decision. Implement, run at least one relevant check, and make the
  project-required commit in the same turn.
- An explicit plan request overrides the direct path.

## Artifact

Write `<plan_root>/<slug>.md`. The nearest `AGENTS.md` or project convention
owns `plan_root`; use `.Codex/plans` only when none exists. Make the plan
self-contained because implementation and final verification receive pasted
contracts, not the planner's session history.

```yaml
---
slug: <kebab-case>
created_at: YYYY-MM-DD
status: draft | approved
spec_ref: docs/specs/<slug>.md | null
source_spec:
  path: docs/specs/<slug>.md | null
  approved_at: YYYY-MM-DDTHH:MM:SS+09:00 | null
  sha: <git blob SHA | null>
approved_plan_revision: <git SHA after explicit approval>
goal: <one measurable sentence>
architecture: <2-3 sentences>
tech_stack: [<item>, ...]
slices:
  - id: 1
    title: <one observable unit>
    files:
      create: [<exact path>, ...]
      modify: [<exact path>, ...]
      test: [<exact path>, ...]
    verification:
      type: unit_test | command | fixture | artifact | visual | custom
      command: <executable command when applicable>
      expected_exit_code: 0
    estimated_minutes: <2-30>
    line_budget: <1-200>
    public_contracts: []
    public_callers: []
    review_checkpoint: skip | required
    checkpoint_reason: null | <one enumerated risk surface>
    decision_needed: false
    user_facing_scenario: null
    recommended: null
    options: []
self_review:
  coverage_gaps: []
  placeholders_found: []
  type_inconsistencies: []
---
```

Each slice body includes exact files, decision-encoding signatures/schemas,
steps, the command, and an independently observable PASS condition. Do not
inline full algorithms or existing files.

## Procedure

1. **Ingest approved intent.** Read the approved spec when present. Carry
   `user_stories`, success criteria, out-of-scope, edge cases, and modules into
   slice contracts. If the spec requires `spec-novelist` and it has not run,
   run that one lightweight pass and fold it before planning.

2. **Map files and real contracts.** Inspect existing owners, callers, schemas,
   and reused contracts before naming files or signatures. Record public caller
   inventory from `rg`/AST instead of guessing.

3. **Create thin vertical slices.** Each slice must deliver one independently
   observable user/system outcome and one PASS artifact. Order dependencies and
   surface a genuinely uncertain, expensive assumption as a throwaway P0 spike
   only when it exists.

   Mark `review_checkpoint: required` only for a slice changing schema/public
   contract; approval/authority/permission/secret/security; persistent artifact,
   latest pointer, idempotency, or concurrency; migration/external state;
   order/capital-allocation/financial-execution semantics; or a foundation used
   by at least two later slices. Mark every other slice `skip`. Size or complexity
   alone is not a trigger.

4. **Encode decisions.** Ask the user only when a choice changes user-visible
   behavior, is hard to reverse, or affects user assets/authority/data. Present
   all such choices in one M1 list with a recommendation and 2-3 consequences
   in plain language. Choose internal HOW decisions with the `decision` lens.

5. **Declare executable verification.** Use exactly one primary type per slice:

   | type | required contract |
   |---|---|
   | `unit_test` | command + expected exit; implementation records real RED and GREEN |
   | `command` | command + expected exit/output |
   | `fixture` | reproducible comparison command |
   | `artifact` | path + existence/match rule |
   | `visual` | observable screenshot/preview criterion |
   | `custom` | command when possible + explicit interpretation |

6. **Self-review once and fix.** Map every requirement to a slice, grep
   placeholders, and compare signatures across slices. Fill all three
   `self_review` arrays; fix non-empty findings before approval.

7. **Get one explicit plan approval.** Change `status: draft` to `approved` and
   record `approved_plan_revision`. Do not insert additional technical approval
   stops.

8. **Run deterministic preflight.** Execute:

   `py -3 <methodos_root>/hooks/common/plan_preflight.py <plan> --repo <project_root>`

   Fix mechanical failures and rerun. A preflight failure does not create a
   semantic review attempt.

9. **Run one conditional decision review.** Dispatch fresh read-only
   `decision-reviewer` only when the approved plan changes security, authority,
   public contracts, user assets/data, irreversible behavior, cross-slice
   ownership, or has at least two user-facing decisions. It inherits the parent
   model and reasoning effort. Do not call it for behavior-preserving structure
   work or ordinary plans.

   - Fold non-blocking findings once; never start a reviewer loop.
   - If folding changes user-visible behavior, authority/data, public contract,
     or irreversibility, show only that scenario delta and obtain the necessary
     user decision. Record the new approved revision.
   - ChatGPT Pro or Claude Fable/Opus runs only on an explicit user request.

10. **Continue automatically.** Implement every slice with local checks and WHY
    commits. Do not run Codex `plan-verify` or routine per-slice `impl-verify`.
    Run one fresh Sol/medium checkpoint only for a slice marked `required` or
    whose actual diff newly matches the predicate. When all planned commits,
    local commands, and required checkpoints are complete, run the single final
    integrated `impl-novelist` gate: attempt 1 full; only failed-review repairs
    use attempt 2+ scoped.

## No placeholders

Reject `TBD`, `TODO`, `implement later`, vague error handling, unnamed tests,
`similar to slice N`, undefined symbols, or slices without exact files and a
reproducible PASS condition.

## Stop conditions

Stop only for a new unresolved WHAT decision, authority/data/user-asset impact,
public-contract change, or irreversible operation. Otherwise continue through
implementation and final verification without asking "진행할까요?".

## Reeval

- If the conditional decision reviewer misses two consequential choices, widen
  its predicate rather than restoring a general plan reviewer.
- If final verification repeatedly finds fictional reused contracts, promote
  that check into `plan_preflight.py` instead of reintroducing `plan-verify`.
