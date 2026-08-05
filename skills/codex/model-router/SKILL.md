---
name: model-router
description: Select, observe, compare, and recommend inline or subagent model routes using task-scoped token, quota, latency, quality, and revision records. Use only when the user explicitly invokes `$model-router`, asks to instrument a task while doing it, asks several models or inline execution to try the same bounded work, assigns a comparison group, or requests a routing recommendation from accumulated records. Preserve provider, effort, modality, and executor identity.
---

# Model Router

Keep the user's real task primary. Measure only enough to decide whether the work belongs inline or on a particular subagent route.

## Choose the mode

- **Observe**: When the user says to use the router while doing one task, execute normally and record that run. Do not launch duplicate workers.
- **Compare**: When the user asks several models to try the same work, run the smallest bounded comparison that answers the question.
- **Recommend**: When the user asks which route fits, summarize relevant valid records. Do not launch candidates unless the user also asks to test them.

## Select a route

Honor current user instruction, then project role/model contracts, then global defaults for the incumbent execution path. Resolve challenger eligibility through the project's model-catalog adapter when one is mandated; otherwise fetch `GET http://127.0.0.1:10100/v1/models?client_version=0.0.0` and use only `models[]` with `visibility=="list"`. Invoke the exact live `slug` and only a listed reasoning effort.

Static examples are not an allowlist. Use accumulated records and task fit first. Useful seed challengers, only when still eligible, include:

- Luna medium for retrieval, transformation, and bounded review.
- Terra medium for closed-context `synthesize + apply` work.
- Qwen 3.8 when contradiction detection, fact cross-checking, or supported image understanding matters.
- OpenCode Free DeepSeek high for text-only mechanical or retrieval slices.

Use `executor + provider + model + effort + modality` as candidate identity. Never merge providers exposing the same model family. Treat DeepSeek routes as text-only for this benchmark policy; record direct image work as `unsupported`, or record a separate vision/OCR-to-text flow as `pipeline`.

## Record one run

1. Classify:
   - `task_type`: `exploration|diagnosis|implementation|review|data-organization|image-understanding`
   - `task_shape`: `retrieve|transform|synthesize|decide`
   - `context_state`: `packet_closed|selected_files|raw_corpus`
   - `judgment_level`: `apply|reconcile|authority_decision`
   - `execution_shape`: `read_only|isolated_candidate|canonical_single_writer`
   - `executor`: `orchestrator|subagent`
   - `dependency_span`: `single_file|bounded_multifile|cross_system`
2. Run `scripts/usage_test.py start` immediately before execution. Prefer `--route-slug`; use explicit `--provider --model` only for recovery or a route that cannot be expressed by the current slug rule. Include `--effort` for a fixed-effort candidate.
3. Run `scripts/usage_test.py finish` immediately after execution. It inherits the locked route and rejects a conflicting route.
4. Let the orchestration session judge the result. Record outcome, optional 0-100 quality score or rank, revision burden, evidence, finish notes, tool rounds, and cost. Workers do not self-rate.
5. Report one compact measurement line after the real task result.

The record scope is `through_finish`; the response generated after finish is not included. Use baseline overrides only for a recovery whose trustworthy start markers were already captured.

If a route is rejected before any usage row exists, still finish the locked run with `--outcome failed`, `--availability rate-limited|provider-unavailable|rejected`, and `--failure-reason`. Use `unsupported` for a known capability mismatch. The recorder writes a zero-token failure instead of dropping the candidate.

## Compare fairly

Freeze one common packet containing the objective, prompt, input references or hashes, allowed tools, timeout, and completion criteria. Pass the same packet file with `--packet` and the same `--comparison-group` to every candidate. A group is `controlled` only when at least two delegated candidates carry the same packet hash and task-condition signature; otherwise treat it as `operational`.

For a delegation decision, default to one inline baseline and one delegated challenger. For a model-only decision, use two delegated candidates. Add a third only when material uncertainty remains. Inline keeps the parent's accumulated context; therefore inline versus delegated is an operational routing comparison, not a pure model ranking.

Use isolated read-only candidates for research, review, and plans. Candidates must not write the canonical artifact. Use one canonical writer after judging outputs. Use worktrees only when implementation ability itself is under test; otherwise use plans or isolated temporary copies.

Do not add a challenger when authority is still open, shared-state mutation cannot be isolated, privacy or tool access differs materially, or duplicate cost is disproportionate.

## Attribute usage safely

OpenCodex-proxied sessions share `~/.opencodex/usage.jsonl`. Treat ledger `timestamp` as request start time and do not treat `conversationId` as session identity. Start each measurement immediately before the inline slice or `spawn_agent`, and finish immediately after completion.

The recorder sorts rows and fails closed when route lock conflicts, request intervals overlap, or input context materially decreases. If several conversation IDs remain, select one only from a known task boundary; never choose the largest or newest candidate. A clean chain cannot distinguish two sequential sessions using the same route tuple, so keep measurement windows narrow.

## Judge records

Use outcomes `ready|minor-revision|major-revision|failed|unsupported|not-rated`. Prefer user judgment; otherwise use `not-rated`. Compare routes in this order: quality, revision burden, request/tool rounds and wall time, then actual or estimated cost.

The summary uses only the latest record per run, excludes explicit superseded records, and rejects `through_finish` records whose usage extends past finish. Controlled and operational observations remain separate. Availability failures remain visible but do not enter the quality success-rate denominator.

Read [pricing.md](references/pricing.md) only when finishing a measured run or comparing costs. Keep actual API charge, subscription Credits, free usage, API-equivalent cost, and estimated subscription allocation separate.

## Commands

```powershell
python scripts/usage_test.py start --task "작업명" --task-type diagnosis --task-shape decide --context-state selected_files --judgment-level reconcile --execution-shape isolated_candidate --executor subagent --dependency-span bounded_multifile --size medium --modality text --comparison-scope bounded-slice --comparison-group GROUP_ID --packet COMMON_PACKET.md --route-slug alibaba-token-plan-intl/qwen3.8-max --effort medium
python scripts/usage_test.py finish --run-id RUN_ID --outcome minor-revision --revision-burden minor --quality-score 82 --rank 2 --evidence "사실 모순 1건 발견" --finish-notes "표 제목 수정 필요" --tool-rounds 6 --billing-mode subscription --pricing-as-of 2026-08-05
python scripts/usage_test.py finish --run-id RUN_ID --outcome failed --availability rate-limited --failure-reason "429 Too Many Requests; retry limit exceeded"
python scripts/usage_test.py summary --comparison-group GROUP_ID
```

Defaults:

- Usage source: `~/.opencodex/usage.jsonl`
- Run states: `~/.codex/usage-tests/runs/`
- Append-only observations: `~/.codex/usage-tests/records.jsonl`

Do not modify the OpenCodex usage source.
