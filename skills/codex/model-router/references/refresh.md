# Refresh

Load this file only when the user asks to update routing recommendations from accumulated records.

## Goal

Turn the append-only raw ledger into a small, current recommendation file that `route` can consume without rescanning records.

## Procedure

1. Load canonical records from `~/.codex/usage-tests/records.jsonl`. Exclude superseded records and `through_finish` records whose usage extends past finish.
2. Group by condition axes: `task_type`, `task_shape`, `context_state`, `judgment_level`, `execution_shape`.
3. Within each group, aggregate per route (`provider + model + effort`): sample count, usable rate, outcome and availability counts, dominant revision burden, median tool rounds, median wall seconds, total tokens, API-equivalent cost, and plan consumption totals.
4. Rank routes: usable rate (higher first), dominant revision burden (none < minor < major), median tool rounds, then API-equivalent cost.
5. Write `routing-recommendations.json` with the recommended route, basis, sample count, confidence (`high` >= 5, `medium` >= 2, `low` otherwise), and generation time.

## Rules

- Raw records are append-only. Only the recommendation file is rewritten.
- Do not rank by cost before quality and revision burden.
- Keep API-equivalent cost and plan consumption separate; do not substitute one for the other.
- Availability failures stay visible but do not enter the usable-rate denominator.
- A group with fewer than `--min-samples` records is marked `sufficient: false` and its recommendation should be treated as provisional.
