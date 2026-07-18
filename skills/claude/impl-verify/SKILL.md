---
name: impl-verify
description: Optional fresh-context check of a risky implementation slice.
---

# Impl Verify

Use once when the slice changes a public caller/producer/consumer contract,
permissions or data authority, external state/concurrency/migration, or when a
semantic review is explicitly requested. Routine slices use local tests and an
exact changed-path check.

Inspect the declared paths and their public callers, producers, consumers, and
failure paths. Independently run the stated tests or commands and return
`PASS`, `NEEDS_CONTEXT`, or concise issue bullets with path/line and a repair
hint. On a repair, rerun only the affected checks once.

Do not require verify-report JSON, candidate/approved hashes, session/model/
effort provenance, terminal packets, commit ceremony, or a report artifact.
