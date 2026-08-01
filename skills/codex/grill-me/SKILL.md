---
name: grill-me
description: Align unclear intent before implementing a new capability, user-visible flow, schema, or unresolved WHAT decision.
---

# Grill Me

Use this interview only when the request leaves the user-visible outcome or
scope unresolved. Existing behavior fixes and closed low-risk edits can proceed
without it.

1. Search the current caller/producer/consumer and existing docs first.
2. Ask one short question at a time, in user terms. Explain the observable
   difference between the options; do not make the user choose implementation
   details that the codebase already settles.
3. Stop when the goal, out-of-scope boundary, affected flow, and acceptance
   checks are explicit, then return that clarified WHAT to the next planning
   step. The current session performs a short actor/flow walk for an ordinary
   spec. Do not dispatch `spec-novelist` from this interview; when later planning
   finds multiple actors or flows, the planning owner applies it once immediately
   before `PLAN_READY`.
4. Save a standalone spec only when it must remain authoritative beyond one
   implementation plan or a named future consumer needs that product contract.
   Do not save one merely because `/plan` follows. User approval is required
   before implementation when the flow, public contract, permissions/data, or
   irreversible operation changes.

Do not create verification reports, provenance records, hashes, terminal
packets, or mandatory reviewer loops. Return the clarified decision in the
conversation when no future maintainer needs a durable record.
