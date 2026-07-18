---
name: impl-novelist
description: Run one optional fresh-context final review when a change introduces a new user/public flow, shared contract or permission/data behavior, external state/concurrency/migration risk, or a multi-slice integration seam.
---

# Impl Novelist

This is a conditional integration review, not a completion ceremony. Ordinary
work closes with local tests and an exact changed-path check. Select this review
once when the risk predicates above apply or when the user asks for a semantic
review. A reviewer returns concise findings to the caller; no report file,
auxiliary completion record, or separate proof document is required.

## Procedure

1. Read the approved requirements (if any), the declared paths, and the
   relevant caller/producer/consumer/failure paths. Do not invent missing
   requirements or scope.
2. Run the declared tests or commands and inspect the resulting behavior. Keep
   checks tied to a user-visible or system-observable invariant.
3. Walk the affected user/system flow once end to end. Return `PASS`,
   `NEEDS_CONTEXT`, or concise issue bullets with path/line and a repair hint.
4. If a finding changes the public contract, authority/data behavior, or user
   decision, stop and request that decision. Otherwise the owning implementer
   may make the smallest repair and rerun the selected checks once.

## Boundaries

- Review only the exact changed paths supplied by the caller; inspect adjacent
  callers and consumers only to establish impact.
- Keep user approval for external work, user data, permissions, database/schema
  changes, public interfaces, concurrency/migrations, and other external state.
- A high-risk review is selective and single-pass. Do not schedule an automatic
  final review for routine work or repeat an unchanged semantic review.
- Transient session targeting may be used to continue a live conversation, but
  it is operational input, never completion evidence.
