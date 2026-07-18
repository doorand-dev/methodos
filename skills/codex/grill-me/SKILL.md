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
   checks are explicit. The current session performs a short actor/flow walk for
   an ordinary spec. Route a spec with multiple actors or multiple flows to one
   fresh `spec-novelist` reader.
4. Save a spec only when the user needs a durable planning document. User
   approval is required before implementation when the flow, public contract,
   permissions/data, or irreversible operation changes.

Do not create verification reports, provenance records, hashes, terminal
packets, or mandatory reviewer loops. Return the clarified decision in the
conversation when no future maintainer needs a durable record.
