---
name: model-router
description: Route, observe, compare, and refresh inline or subagent model routes using task-scoped token, quota, latency, quality, and revision records. Use only when the user explicitly invokes `$model-router`, asks which model to delegate a task to, asks to instrument a task while doing it, asks several models or inline execution to try the same bounded work, assigns a comparison group, or asks to update routing recommendations from accumulated records. Preserve provider, effort, modality, and executor identity.
---

# Model Router

Keep the user's real task primary. Measure only enough to decide whether the work belongs inline or on a particular subagent route.

## Choose the mode

- **Route**: When the user asks which model to delegate a task to, read the latest `routing-recommendations.json` and pick one route. Do not launch candidates or rescan raw records.
- **Observe**: When the user says to use the router while doing one task, execute normally and record that run. Do not launch duplicate workers.
- **Compare**: When the user asks several models to try the same work, run the smallest bounded comparison that answers the question.
- **Refresh**: When the user asks to update recommendations from accumulated records, aggregate valid records and regenerate `routing-recommendations.json`. Only refresh reads the full raw ledger.

## Select a route

Honor current user instruction, then project role/model contracts, then global defaults for the incumbent execution path. Resolve challenger eligibility through the project's model-catalog adapter when one is mandated; otherwise fetch `GET http://127.0.0.1:10100/v1/models?client_version=0.0.0` and use only `models[]` with `visibility=="list"`. Invoke the exact live `slug` and only a listed reasoning effort.

Static examples are not an allowlist. Use accumulated records and task fit first. Useful seed challengers, only when still eligible, include:

- Luna medium for retrieval, transformation, and bounded review.
- Terra medium for closed-context `synthesize + apply` work.
- Qwen 3.8 when contradiction detection, fact cross-checking, or supported image understanding matters.
- OpenCode Free DeepSeek high for text-only mechanical or retrieval slices.
- OpenCode Go DeepSeek high for bounded verification slices. Controlled group `inventory-crosscheck-260805` (review/decide, n=1): it beat Sonnet medium and Sonnet high, and raising Sonnet effort above medium did not improve this task type.

Use `executor + provider + model + effort + modality` as candidate identity. Never merge providers exposing the same model family. Treat DeepSeek routes as text-only for this benchmark policy; record direct image work as `unsupported`, or record a separate vision/OCR-to-text flow as `pipeline`.

### ChatGPT web (chatgpt.com) as a review route

ChatGPT web, driven through the Codex in-app browser (skill `chatgpt-inapp-review`) or
agbrowse (`ask-chatgpt-pro`, `web-ai`), is a separate route class from the OpenCodex
model list above: it is not an API call, has no per-token cost visibility, and is
selected by reasoning-effort label (즉시/중간/높음/매우높음/Pro) rather than a slug.
Record it as `executor=orchestrator` (or `subagent` if a delegated agent drives the
browser), `provider=chatgpt-web`, `model=<effort-label>`, with `plan_consumption`
left null (no observable per-request debit) and `api_equivalent_usd` left null unless
a rate basis for that effort tier becomes available.

**When to reach for this route at all**: only when the user explicitly asks for
ChatGPT web / in-app-browser / agbrowse review, not as a silent substitute for an
OpenCodex model route. This is a second-opinion / cross-check surface, not a default
execution path.

**Which effort tier to use, from one comparison run (`inapp-review-effort-260805`,
n=1 per tier, KIAS institutional-report review task — see
`chatgpt-inapp-review/references/effort-comparison-260805.md` for full evidence):**

| Tier | Use when | Cost signal |
|---|---|---|
| 즉시/중간 | Fast sanity check; user needs an answer in under a minute | ~20-30s wall time |
| 높음 | Default for a real review — best depth-per-minute; first tier to do concrete named-entity fact cross-checks | ~3 min wall time |
| 매우높음 | Same cost tier as 높음 but reorganizes findings into finer sub-cases; lateral move, not a strict upgrade | ~2-3 min wall time |
| Pro | Only for high-stakes review where one extra unique catch justifies several extra minutes and a UI trap (must not click the mid-generation "지금 답변 받기" button, which truncates the answer) | several min longer than 매우높음; no auto-retry if user force-answers early |

Escalating effort did not change *what class* of problem was found (all tiers
converged on the same core issues); it changed granularity, named-entity specificity,
and the odds of one additional unique catch. Treat 높음 as the default; only escalate
to Pro when the review feeds a high-stakes decision and the wait is acceptable. Do not
assume this ordering holds for other task types (e.g. code review, math) without a
separate comparison run — record a new group before generalizing.

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
4. Let the orchestration session judge the result. Record outcome, optional 0-100 quality score or rank, revision burden, evidence, finish notes, tool rounds, API-equivalent cost, and observed plan consumption. Keep either unavailable cost axis null or empty; never substitute one for the other. Workers do not self-rate.
5. Report one compact measurement line after the real task result.

The record scope is `through_finish`; the response generated after finish is not included. Use baseline overrides only for a recovery whose trustworthy start markers were already captured.

If a route is rejected before any usage row exists, still finish the locked run with `--outcome failed`, `--availability rate-limited|provider-unavailable|rejected`, and `--failure-reason`. Use `unsupported` for a known capability mismatch. The recorder writes a zero-token failure instead of dropping the candidate.

## Refresh recommendations

Run `refresh` when the user asks to update routing recommendations from records, not on every task. It reads the full valid ledger, groups records by condition axes, ranks routes per group by usable rate, dominant revision burden, median tool rounds, then API-equivalent cost, and writes the single source of truth `routing-recommendations.json` with sample counts, confidence tiers, basis, and generation time. Raw records stay append-only; only the recommendation file is rewritten.

Read [refresh.md](references/refresh.md) only when running a refresh. Do not read the full raw ledger for normal routing.

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

Read [pricing.md](references/pricing.md) only when finishing a measured run or comparing costs. Always show API-equivalent cost and actual plan consumption as separate axes. Keep actual API charge, subscription Credits, free usage, and estimated subscription allocation separate as well.

## Commands

```powershell
python scripts/usage_test.py start --task "작업명" --task-type diagnosis --task-shape decide --context-state selected_files --judgment-level reconcile --execution-shape isolated_candidate --executor subagent --dependency-span bounded_multifile --size medium --modality text --comparison-scope bounded-slice --comparison-group GROUP_ID --packet COMMON_PACKET.md --route-slug alibaba-token-plan-intl/qwen3.8-max --effort medium
python scripts/usage_test.py finish --run-id RUN_ID --outcome minor-revision --revision-burden minor --quality-score 82 --rank 2 --evidence "사실 모순 1건 발견" --finish-notes "표 제목 수정 필요" --tool-rounds 6 --billing-mode subscription --api-equivalent-usd 0.14 --plan-consumption credits=0.67 --plan-consumption quota_7d_percent=0.02 --pricing-as-of 2026-08-05
python scripts/usage_test.py finish --run-id RUN_ID --outcome failed --availability rate-limited --failure-reason "429 Too Many Requests; retry limit exceeded"
python scripts/usage_test.py summary --comparison-group GROUP_ID
python scripts/usage_test.py refresh --min-samples 2
python scripts/usage_test.py route --task-type review --task-shape decide --context-state packet_closed --judgment-level reconcile --execution-shape read_only
```

Defaults:

- Usage source: `~/.opencodex/usage.jsonl`
- Run states: `~/.codex/usage-tests/runs/`
- Append-only observations: `~/.codex/usage-tests/records.jsonl`
- Single source of truth recommendations: `~/.codex/usage-tests/routing-recommendations.json`

Do not modify the OpenCodex usage source.
