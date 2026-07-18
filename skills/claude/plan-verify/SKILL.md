---
name: plan-verify
description: Optional advisory check of an approved plan when risk or unresolved scope warrants it.
---

# Plan Verify

Select this check only when the plan changes a public flow/contract, authority
or data behavior, an irreversible operation, external state/concurrency/
migration, or crosses several independent slices. Routine plans close after
preflight, local tests, and exact-path review.

Read the plan and inspect its caller/producer/consumer/failure impact. Run the
declared preflight or tests. Return concise `PASS`, `NEEDS_CONTEXT`, or issue
bullets with path/line and the missing decision. The check is advisory and does
not auto-rewrite plans or start a verify loop.

Do not require JSON reports, lineage hashes, session/model/effort attestation,
terminal packets, or red-green commit ceremonies.
