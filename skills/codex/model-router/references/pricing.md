# Pricing Reference

Load this file only when a measured run needs a cost field or when the user asks for cost comparison. Rates and promotions are time-sensitive; preserve the stated basis date and replace stale terms rather than silently carrying them forward.

## Cost fields

Calculate `api_equivalent_usd` only when a rate basis is available. Use:

`uncached_input × base_rate + cache_read × read_rate + cache_creation × write_rate + output × output_rate`, divided by 1M.

Do not double-count reasoning output. When cache creation is not exposed separately, omit that term and state the limitation.

Always expose both comparison axes when reporting cost. Keep the unavailable axis null or empty rather than substituting the other:

- `api_equivalent_usd`: what the same tokens would cost at the stated standard API rates.
- `plan_consumption`: observed plan debit as one or more `unit: value` pairs, such as `credits`, `quota_5h_percent`, or `quota_7d_percent`.

Keep these supporting values separate:

- `usd_cost`: observed actual API charge.
- `credits_used`: observed subscription Credits.
- `estimated_credits` and `estimated_subscription_usd`: estimated subscription allocation.
- Free routes: actual cost remains $0 even when an API-equivalent value is recorded.

Pass observed plan values as repeated `--plan-consumption UNIT=VALUE` arguments. `--credits-used` remains supported and is mirrored to `plan_consumption.credits`. Promotions and night discounts affect plan consumption, not API-equivalent cost.

Do not collapse the two axes into one ranking. Report quality per API-equivalent dollar and quality per observed plan debit separately when enough observations exist. Use actual cash charge as a third operational view.

## Rates as of 2026-08-04

Rates below are per 1M tokens in uncached input / cache read / output order.

- OpenAI standard API: Sol $5 / $0.50 / $30; Terra $2 / $0.20 / $12; Luna $0.20 / $0.02 / $1.20. For a request above 272K input tokens, apply 2x input and 1.5x output to that whole request. Price separately reported cache creation at 1.25x uncached input. Basis: official [OpenAI model comparison](https://developers.openai.com/api/docs/models/compare).
- Anthropic standard API: Fable 5 $10 / $1 / $50; Opus 5 $5 / $0.50 / $25. Sonnet 5 uses introductory $2 / $0.20 / $10 through 2026-08-31, then $3 / $0.30 / $15. Price cache creation at 1.25x input for a default 5-minute write or 2x for an explicitly requested 1-hour write. Basis: official [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- Alibaba DeepSeek: use DeepSeek standard API rates, currently $0.14 uncached input / $0.0028 cached input / $0.28 output.
- OpenCode Free DeepSeek: API-equivalent is one-sixth of the DeepSeek standard result; actual cost remains $0.
- Qwen 3.8: keep API-equivalent cost null unless an official applicable API price is available. Estimate Token Plan Credits as described below.

Record `pricing_basis` and `pricing_as_of` for every non-null cost estimate.

## Qwen Token Plan estimate

Calibration observation:

`193 uncached + 15,360 cached + 47 output = 0.674736697 promotional Credits`

Use the nearest official Qwen Max relative ratio `uncached:cached:output = 1:0.2:3`. The observation was under Max Preview's 10% daytime promotion, so divide it by `0.10` before fitting standard Credit coefficients. This assumes Preview and production Max share the same underlying standard coefficients; state that assumption.

After calculating `estimated_standard_credits`, apply:

- Production `qwen3.8-max`: factor `1.0` normally; `0.5` from 22:00 through 08:00 UTC+8.
- `qwen3.8-max-preview`: factor `0.10` normally; `0.02` during the same window because the additional night discount stacks on the preview promotion.

If a run crosses the boundary, split by request timestamp when possible; otherwise mark the estimate uncertain.

Convert Credits to subscription allocation with:

`$18/month × 12/52 ÷ 10,000 weekly Credits`

Record `credit_promotion_factor`, `promotion_basis`, `estimate_basis`, and the observation date. Treat all Qwen coefficients and promotion factors as estimates or limited-time terms. Refit or replace them when promotion terms change, an official Qwen 3.8 API price appears, or exact quota deltas provide enough equations.
