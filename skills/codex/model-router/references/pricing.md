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

## Rate basis

This publication contains no fixed model prices, subscription promotions, or private calibration samples. At measurement time, look up the provider's official price for the exact model, date, service tier, input-length bracket, and cache behavior. Record `pricing_basis` and `pricing_as_of` for every non-null estimate.

Do not assume Fast/priority pricing unless the request or authoritative usage record establishes that tier. If the tier is unavailable, label a standard-rate calculation as an assumption. Use actual request-level token categories; cache-read tokens are part of input, and reasoning output must not be added twice.

Only estimate subscription allocation from the adopter's documented plan and observable debit. Keep unavailable values null. Promotional terms, conversion factors, and calibration observations belong with that measurement's evidence, not in a reusable default.
