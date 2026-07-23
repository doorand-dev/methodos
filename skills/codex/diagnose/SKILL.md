---
name: diagnose
description: Diagnose bugs with a bounded fast path by default. Use the full reproduce-hypothesise-instrument-regression loop only for hard, non-local, intermittent, performance, concurrency, security/data, or otherwise costly bugs.
---

# Diagnose

Choose the smallest route that can falsify the suspected defect. A bug report,
exception, or failed command alone does not justify the full hard-bug loop.

## Fast path — default

Use this route when the observed symptom, owning seam, smallest fix, and one
focused oracle are already clear, and no high-risk boundary below applies.

1. State the exact symptom and owner seam.
2. Run the focused oracle once to reproduce the symptom.
3. Apply the smallest owner-seam fix.
4. Run the same oracle once to confirm the change.
5. Report the changed paths, oracle result, and any remaining real risk.

The oracle may be an existing focused test, one command, fixture comparison,
runtime smoke, or artifact check. Do not create a regression test merely to
satisfy this workflow. Do not generate 3–5 hypotheses, add instrumentation,
build a new harness, run a broad suite, or write a post-mortem on this route.

Escalate to the hard path only when the focused oracle fails to reproduce the
reported symptom, the owner seam remains uncertain, or the change crosses one
of the hard-path boundaries.

## Hard path

Use the full loop for a non-local or costly uncertainty: intermittent/flaky
behavior, performance regression, concurrency or exactly-once state, security
or user-data behavior, migration/external state, several plausible owner seams,
or a failure whose focused oracle is missing or contradictory.

### 1. Build a feedback signal

Prefer the smallest deterministic signal that reaches the real bug pattern:
focused test, CLI/HTTP invocation, fixture diff, runtime trace, or a minimal
replay. Create a temporary harness only when existing seams cannot reproduce the
bug. Improve reproduction rate only as much as needed to distinguish causes.

### 2. Reproduce and minimise

Confirm the user's exact symptom, then minimise the input or path without
changing the failure mode. Do not substitute a nearby failure.

### 3. Hypothesise

Generate 3–5 ranked, falsifiable hypotheses only on this hard path. Map each
hypothesis to one prediction. Share the ranking when user domain knowledge could
materially change the order; do not make it a blocking ceremony.

### 4. Instrument

Use one targeted probe per prediction. Prefer debugger/REPL inspection and
boundary logs. Do not log everything. Measure performance before changing it.

### 5. Fix and lock the regression

Write a regression test before the fix only when a correct seam exists and the
failure could silently recur. Otherwise use the minimal reproducer as the oracle
and record why a durable test would be misleading or disproportionate.

Apply the smallest fix, run the focused oracle, and recheck only affected
commands. A full regression is owned by the lifecycle contract in `impl`, not
by this skill.

### 6. Clean up

Remove temporary instrumentation and throwaway harnesses. State the confirmed
cause and remaining risk. Recommend architecture follow-up only when the missing
seam materially caused the defect; do not create a report or follow-up task by
default.
