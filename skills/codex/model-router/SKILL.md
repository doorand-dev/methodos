---
name: model-router
description: Explicitly measure and record a real task's provider, model, reasoning effort, task conditions, token usage, quota charge, latency, and outcome; also run the same bounded slice across isolated model candidates when the user asks for parallel model testing. Use only when the user explicitly invokes `$model-router`, says to use the model-routing skill, asks to instrument a task while doing it, assigns a comparison group, asks several models to try the same work, or asks for recommendations from accumulated routing-test records. Distinguish providers even when they expose the same model, and treat image-capable and text-only routes separately.
---

# Test Model Routing

Measure the requested work without turning the work into a large benchmark project. Preserve the user's task as the primary objective; instrumentation is secondary.

## Record a task

1. Classify `task_type` as one of `exploration`, `diagnosis`, `implementation`, `review`, `data-organization`, or `image-understanding`. Also record `task_shape` (`retrieve|transform|synthesize|decide`), `context_state` (`packet_closed|selected_files|raw_corpus`), `judgment_level` (`apply|reconcile|authority_decision`), `execution_shape` (`read_only|isolated_candidate|canonical_single_writer`), and `dependency_span` (`single_file|bounded_multifile|cross_system`). Keep `task_subtype` as human-readable notes, not an aggregation key. Set size and modality using best judgment.
2. Run `scripts/usage_test.py start` before substantial work. Include `--comparison-group` only when the user intends to repeat materially the same task. Include important input files with repeated `--input` arguments so their hashes can be checked.
3. Perform the user's task normally. Do not weaken, truncate, or reshape it merely to improve the measurement.
4. Near the end, run `scripts/usage_test.py finish`. Pass exact `--provider`, `--model`, and `--effort` when known. If multiple conversations are reported, select the current task's conversation ID from the candidates and rerun with `--conversation-id`; never silently combine unrelated tasks.
5. Report one compact measurement line after the actual task result. Distinguish actual Credits/cost from unknown or estimated values.

The final model response generated after `finish` may not yet be present in the usage log. Label the record `through_finish`; do not claim it is whole-thread billing.

Use `--baseline-start-ms` and `--baseline-offset` only to recover a task whose trustworthy start markers were captured before the script could run, such as dogfooding this skill's own creation.

## Discover eligible routes

Before choosing a candidate, fetch `GET http://127.0.0.1:10100/v1/models?client_version=0.0.0`. Use only entries in `models[]` whose `visibility` is exactly `"list"`. Use each `slug` verbatim. Accepted efforts are only the values in `supported_reasoning_levels[].effort`; omit effort when it is absent. Do not infer routes or efforts from names or stale files. Candidates for explicit comparisons come from user-designated routes or accumulated routing-test records; keep this skill free of static route lists.

## Preserve route identity

Use `provider + model + effort + modality` as the candidate identity. Never merge routes from different providers merely because they expose the same model family. Record free routes with `billing_mode=free`; still retain latency, retries, failures, and rate-limit effects.

For this user's benchmark policy, treat every DeepSeek route as text-only even if catalog modality metadata says otherwise. Mark a direct image job `unsupported`; a separately measured vision/OCR step followed by a DeepSeek text job is allowed and must be recorded as a `pipeline`.

Treat Luna effort levels such as `low`, `medium`, and `high` as different candidates. Do not infer a fixed reasoning surcharge when the provider does not publish one.

## Handle images

- Set `modality=image` when the candidate directly receives images.
- Mark a text-only model asked to directly inspect an image as `unsupported`, not `failed`.
- Set `modality=pipeline` when a vision/OCR stage converts images before a text model processes the result. Record the pipeline description in `--notes`; do not present this as the text model's standalone vision quality.

## Compare fairly

Records sharing a comparison group are strict comparisons only when their input hashes, task objective, tools, effort policy, and completion condition match. If they differ, present them as operational observations rather than controlled model rankings.

For a same-job comparison, freeze one immutable common packet containing the prompt, input hashes, tools, timeout, and completion criteria. Run one fresh conversation per candidate and assign every run the same `comparison_group`. After all candidate outputs exist, the orchestration session judges quality and records the outcome, optional score or rank, evidence, and free-form notes. Workers do not self-rate.

For ordinary unmatched tasks, report task cost and outcome but do not infer model superiority. Recommend routing only after multiple relevant observations exist; otherwise state that evidence is insufficient.

## Embed a challenger slice

Distinguish recommendation from execution. If the user only asks which model fits, recommend routes and identify a testable slice without launching duplicates. If the user says to run models in parallel, try several models, or test the same work, execute one bounded duplicate slice during the real task.

Choose a slice only when one immutable packet can define the same objective, inputs, tools, timeout, and completion criteria for every candidate. Prefer a useful unit already present in the workflow: one requirement item, one contradiction check, one bounded search query, one document section, or one isolated implementation plan. Do not duplicate the entire workflow when a representative slice is available.

Run two or three candidates:

- Include the incumbent route that would normally receive the slice.
- Use `gpt-5.6-luna/medium` as the default text challenger for retrieval, transformation, and bounded review.
- Use `gpt-5.6-terra/medium` when the authority and direction are closed, context is a bounded packet, judgment is `apply`, and the output is an isolated candidate or reversible bounded implementation.
- Add `alibaba-token-plan-intl/qwen3.8-max/medium` only when contradiction detection, fact cross-checking, or supported image understanding is material.
- Add `opencode-free/deepseek-v4-flash-free/high` only for text-only mechanical or retrieval slices; never send it direct images.

Give every candidate the frozen packet in a fresh conversation and the same `comparison_group`; record `comparison_scope=bounded-slice`. Candidates must return isolated outputs and must not write the canonical artifact. The orchestration session judges quality before considering cost, records revision burden and notes, selects any useful result, and leaves canonical writing to one writer.

Do not add a challenger when the slice still contains an open authority decision, the candidates would mutate shared state, privacy or tool access differs materially, or duplicate cost is disproportionate. In those cases, record the operational run only.

Treat Terra medium as a conditional candidate, not a general implementation default. Its current observed sweet spot is `packet_closed + synthesize/apply + isolated_candidate or canonical_single_writer + bounded_multifile`; escalate open authority, raw-corpus contract design, or cross-system reconciliation to the appropriate lead.

## Decide how to execute

- Use parallel read-only work for design, research, and review.
- For shared-file changes, use read-only plans first, then one canonical writer.
- Use worktrees only when implementation ability itself is being benchmarked and a Git repository exists.
- When no Git repository exists, use isolated temporary copies.
- Parallel writes are allowed only for mechanically disjoint write sets.

Use native `spawn_agent`. If it rejects a route, report the rejection and do not substitute another route. OpenCodex-proxied UI and subagent requests land in `~/.opencodex/usage.jsonl`.

## Cost reporting

Calculate and record `api_equivalent_usd`, `pricing_basis`, and `pricing_as_of` for every measured run. Use `uncached_input*base_rate + cache_read*read_rate + cache_creation*write_rate + output*output_rate`, dividing token counts by 1M; never double-count reasoning. When the log does not expose cache creation separately, omit that term and state the limitation. Keep API-equivalent cost separate from actual API cost, subscription Credits, and free usage.

Judge routing cost in this order: observed `usd_cost` or `credits_used`; estimated subscription cost based on an observed quota rule; then API-equivalent cost. Never call API-equivalent cost the actual charge for a subscription or free route. Compare quality-adjusted cost only across materially equivalent tasks; otherwise report each run's cost without ranking efficiency.

Use these rates per 1M tokens as of 2026-08-04:

- OpenAI standard API: Sol $5/$0.50/$30, Terra $2/$0.20/$12, Luna $0.20/$0.02/$1.20 for uncached input/cache read/output. For each request above 272K input tokens, apply 2x input and 1.5x output to that whole request before summing the run. Price separately reported cache creation at 1.25x uncached input. Basis: official [OpenAI model comparison](https://developers.openai.com/api/docs/models/compare).
- Anthropic standard API: Fable 5 $10/$1/$50 and Opus 5 $5/$0.50/$25 for uncached input/cache read/output. Sonnet 5 uses its introductory $2/$0.20/$10 rates through 2026-08-31, then $3/$0.30/$15. Price cache creation at 1.25x input for the default 5-minute write or 2x for an explicitly requested 1-hour write. Basis: official [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- Alibaba DeepSeek: DeepSeek standard API rates, currently uncached input $0.14/M, cached input $0.0028/M, output $0.28/M.
- OpenCode Free DeepSeek: one-sixth of the DeepSeek standard API-equivalent result; actual cost remains $0.
- Qwen 3.8: keep API-equivalent cost `null`, but record an explicitly estimated Token Plan cost. Calibrate absolute Credits from the daytime Max Preview observation `193 uncached + 15,360 cached + 47 output = 0.674736697 promotional Credits`; use the nearest official Qwen Max relative ratio `uncached:cached:output = 1:0.2:3`. Because Max Preview's daytime promotion charges 10% of its standard rate, divide that observation by `0.10` before estimating standard Credits. This also assumes Preview and production Max share the same underlying standard Credit coefficients; state that assumption.

Apply promotions separately after calculating `estimated_standard_credits`: production `qwen3.8-max` uses factor `1.0` normally and `0.5` from 22:00 through 08:00 UTC+8; `qwen3.8-max-preview` uses factor `0.10` normally and `0.02` during that window because its additional night discount stacks on the 90% promotion. Record `credit_promotion_factor`, `promotion_basis`, and `estimated_credits = estimated_standard_credits × credit_promotion_factor`. If a run crosses the boundary, split by request timestamp when possible; otherwise label the estimate uncertain. Convert estimated Credits to subscription allocation with `$18/month × 12/52 ÷ 10,000 weekly Credits`.

Label the Qwen result and all promotion factors as estimates or time-limited terms, not an official permanent price. Record the page's terms and observation date in `estimate_basis`/`promotion_basis`. Replace them when the promotion changes, an official Qwen 3.8 API price is published, or exact per-run quota deltas provide enough equations to fit cached-input, uncached-input, and output coefficients. Include API-equivalent or estimated subscription USD in the task result table and record the basis and date used.

Use the outcome scale `ready`, `minor-revision`, `major-revision`, `failed`, `unsupported`, or `not-rated`. Prefer the user's judgment. If no judgment is available, use `not-rated` rather than inventing a quality score. Compare routes in this order: quality, revision burden, request/tool rounds and wall time, then cost.

## Commands

Use the bundled standard-library script:

```powershell
python scripts/usage_test.py start --task "작업명" --task-type diagnosis --task-subtype "단일 요구항목 검토" --task-shape decide --context-state selected_files --judgment-level reconcile --execution-shape isolated_candidate --dependency-span bounded_multifile --size medium --modality text --comparison-scope bounded-slice --comparison-group GROUP_ID
python scripts/usage_test.py finish --run-id RUN_ID --provider alibaba-token-plan-intl --model qwen3.8-max --effort medium --outcome not-rated --billing-mode subscription --estimated-standard-credits 243.06 --credit-promotion-factor 1.0 --estimated-credits 243.06 --estimated-subscription-usd 0.10096 --estimate-basis "Estimate: daytime Max Preview observation normalized by 0.10; assumes Preview and production Max standard coefficients match" --promotion-basis "qwen3.8-max daytime factor 1.0; limited-time night factor 0.5 at 22:00-08:00 UTC+8" --pricing-as-of 2026-08-04
python scripts/usage_test.py summary --task-type diagnosis
```

Default sources and outputs:

- Usage source: `~/.opencodex/usage.jsonl`
- Run states: `~/.codex/usage-tests/runs/`
- Append-only observations: `~/.codex/usage-tests/records.jsonl`

Do not modify the OpenCodex usage source.
