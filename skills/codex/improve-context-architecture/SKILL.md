---
name: improve-context-architecture
description: |
  Find structural deepening opportunities in a context system: replace repeated model routing judgment, shallow document chains, ambiguous authority, manual loading conventions, or fragile context lifetimes with a higher-leverage topology and mechanical contracts where justified. Explicit trigger only: use when the user directly says "improve context", "improve context architecture", "improve-context-architecture", "/improve-context-architecture", "컨텍스트 아키텍처 개선", "컨텍스트 체계 자체를 개선", or explicitly asks for a fundamental context-system redesign. Do not trigger for a local routing link, one stale document fix, AGENTS pointer edit, hook repair, packet review, or context-gc sweep.
---

# Improve Context Architecture

Turn repeated context friction and system-wide audit findings into deeper
context machinery: fewer decisions at the reader, smaller point-of-use packets,
clearer authority and lifetime, and real runtime ingresses. This skill proposes
new compositions; it does not merely repair stale instances.

## Boundary

Use this skill only after an explicit architecture-level request. Do not absorb:

- immediate incident capture (`blame-context`);
- scoped or full stale-contract collection (`context-gc`);
- focused packet sufficiency (`context-novelist`);
- a closed local route or documentation repair (`impl`).

Do not implement a candidate until the user selects it and the normal decision,
plan, and implementation gates close its behavior, paths, and verification.

## Inputs

Start with the smallest available evidence set:

1. the requested context-system scope and real runtime ingresses;
2. relevant open or uncertain entries from
   `<workspace>/.Codex/context-friction.md`, when present;
3. the latest relevant `context-gc` findings, when available;
4. current AGENTS, skills, hooks, maps, indexes, resolvers, handoffs, plans, and
   consumers on the marked paths;
5. runtime documentation only where the actual loading or lifetime behavior is
   uncertain.

Neither incidents nor a prior GC run are mandatory. They increase evidence but
must not become invented prerequisites.

## Deepening scan

Model the current context topology as nodes, runtime ingresses, and point-of-use
edges. Look for structural leverage rather than more prose:

- the model repeatedly makes the same crisp routing decision;
- a required target depends on memory or undocumented convention;
- many readers traverse the same shallow chain of pointers;
- authority or lifetime is copied across several surfaces;
- always-on context pays a recurring cost for a rare decision;
- manual handoff or compaction recovery can become an explicit ingress;
- stale contracts recur because no producer-consumer check exists;
- one semantic decision can remain LLM-owned while its invariants become a
  checker, schema, hook, or fixture;
- a resolver, adapter, or index would remove more interface complexity than it
  adds.

Apply a deletion test to each proposed layer: if deleting it merely spreads the
same routing, authority, and failure logic back across many readers, it has
depth. If deleting it removes complexity, it was another shallow layer.

## Candidate contract

Present a small ranked set. For every candidate include:

```text
Name:
Evidence:
Current topology and first failing decision:
Target topology:
Edges added, removed, or changed:
Mechanical contract:
LLM judgment retained:
Migration and rollback boundary:
Expected reduction in reader burden:
Risks and authority conflicts:
Recommendation: strong | worth-exploring | speculative
```

End with one top recommendation and ask the user which candidate to pursue.
Do not create an ADR, plan, report file, resolver, hook, or schema before that
selection. If no candidate passes the deletion test or has concrete evidence,
return that the current system should remain unchanged.

## After selection

Once the user selects a candidate:

1. resolve user-visible and architecture choices with the decision gate;
2. define exact producers, consumers, authority, lifetime, failure behavior,
   write paths, and verification;
3. use `context-novelist` to walk the proposed reader's first decision at each
   changed point of use;
4. plan and implement only the selected composition;
5. use `context-gc` after implementation to check for superseded, duplicate,
   orphaned, or stale surfaces left by the migration.

## Dedicated evidence store

`.Codex/context-friction.md` remains the sole incident store. This skill reads
and resolves entries but does not create a second architecture backlog or copy
incident facts into a new report. Mark resolved entries only when the selected
change is implemented and its verification passes. Change only `status: open`
to `status: resolved`; never rewrite `closed`, which means context was not the
cause.
