---
name: context-novelist
description: |
  Audit and design minimal sufficient context packets with progressive disclosure. A context novelist lives as the next reader of a context packet, not as the author: it walks the reader's first decision at the point of use and reports where the packet fails.
  Use for a prompt, handoff, AGENTS.md, SKILL.md, lane, plan, review packet, live session, point-of-use route, or multi-agent workflow audit; for MSC-PD, progressive disclosure, fresh-context review, or context novelist requests; and when a change creates or alters persistent future-session context topology. Do not own immediate incident capture, scoped/full context garbage collection, or context-system architecture deepening; those belong to blame-context, context-gc, and improve-context-architecture. Apply this only as the focused point-of-use validation lens when those workflows change a route or packet.
  Do not use this as the generic "novelist" reviewer for spec or implementation narrative dry-runs; those are the spec-novelist and impl-novelist agents.
---

# Context Novelist

Use this skill as a fresh-context audit lens. A context novelist lives as the
next reader of a context packet, not as its author. It walks the reader's first
decision at the point of use and reports where the packet fails.

Decide the smallest context packet that lets a future agent do the next task
safely, without inheriting stale narrative or evidence dumps.

This is a skill, not a replacement for narrative novelist agents. Use
independent review only when author intent, prior conclusions, or a proposed
fix could bias semantic judgment and the target plus question can be closed as
a standalone packet. If the user explicitly names an agent or isolation mode,
follow that direction unless a higher-priority contract or runtime constraint
prevents it. For independent review, spawn the subagent with
`fork_turns="none"`, then send this skill and only the proposed packet or target
files. Never use `all` or a recent turn count; the agent cannot discard
inherited conversation after spawning.
Context-novelist never satisfies or skips a required `spec-novelist` or
`impl-novelist` check. When both checks apply, keep them independent and run
them in parallel.

## Trigger and routing boundary

Apply this skill when the request audits a focused context packet or point of
use, or when a change creates or changes how a future session discovers,
selects, loads, or hands off persistent context. The latter includes AGENTS,
skills, maps, indexes, resolvers,
workmaps, handoffs, hooks, and multi-agent or job entry routes, even if the
request does not say “context audit”.

Keep companion ownership separate:

- `blame-context` captures one live misread in the current session without a
  subagent.
- `context-gc` inventories and sweeps stale, unreachable, expired, duplicate,
  or contradictory context over a named or full scope.
- `improve-context-architecture` proposes a new context composition when the
  existing topology itself is the limitation.

Do not perform those workflows here. Re-enter this lens only to validate a
specific reader's first decision or a proposed/changed point-of-use edge.

Keep runtime-specific loading details lazy. Read [the Codex context lifetimes
reference](references/codex-context-lifetimes.md) only when the runtime is Codex or when
the task asks about Codex session, turn, skill, hook, compaction, or memory
loading.

## Graph audit

Model the topology as a directed graph, not a fixed chain. Nodes may be any
context artifact or runtime ingress: AGENTS, a global or project skill, a
capability map, adapter, resolver, script, index, handoff, hook, plan, job
entry, memory, or another named artifact. A skill may read a capability map,
contain an adapter or resolver, invoke a script, or point to another skill.
Do not prescribe a resolver, index, or `contract_ref`; describe only the
composition that actually exists.

For every edge, record and audit:

```text
From | Trigger | Action | To | Lifetime | Authority | Failure
```

Use the fields literally: identify the producer, the runtime or user event
that activates it, the load/select/inject/hand-off action, the resulting target,
how long the edge applies, which source wins, and what happens when it is
missing, stale, duplicated, cyclic, or rejected. Distinguish an edge that is
automatic from one that requires a real runtime ingress or an explicit user
action.

Core invariant: every non-automatic point-of-use (POU) target must be reachable
from at least one real runtime ingress. Flag orphan targets, ambiguous or
duplicate authority, cycles, stale edges, and silent fallback. An artifact that
exists but has no reachable trigger is not complete; a target reached only by
model memory or an undocumented convention is not reachable.

Audit the next reader's first decision at each POU: reader, trigger, minimum
packet, authority, lifetime, and failure behavior must be explicit. Preserve
progressive disclosure: route first, then load only the contract, schema, test,
artifact, or evidence required for that decision. Do not read cold history,
archives, long evidence, or prior conclusions unless stale state or provenance
is the target. Keep case-packet boundaries and fresh-context review principles
when they remain compatible with the graph.

## Case packets

Use the smallest matching packet. If several apply, start with the narrowest
and add only named dependencies.

| Case | Include | Exclude by default |
|---|---|---|
| Code change | User goal, touched files, nearest AGENTS.md, relevant tests/checkers, named contract/schema | Whole repo docs, old plans, unrelated dirty files |
| Spec or plan | Approved spec/plan, acceptance criteria, directly named ADRs/contracts, open decisions | All ADRs, full chat history, implementation logs |
| Lane/orchestration | Relevant lane header before History, active program block, named checker/contract, current call | Lane History, evidence logs, consumed calls |
| External/fresh review | Objective, exact files/excerpts, audit questions, output contract, forbidden assumptions | Prior conclusion, intended fix, broad repo dump |
| Evidence/data | Schema, manifest/hash, aggregate counts, failing examples, source authority | Full raw corpus unless sampling/provenance requires it |
| UI/design | Target URL or screenshots, design-system entrypoint, current component files, acceptance criteria | Old mock archives, unrelated variants |
| AGENTS/SKILL/knowledge | Target, consumer trigger, POU path, duplication/staleness checks | Mirror docs, process history |
| Runtime/session audit | Current intent, injected routing context, loaded routing artifacts, recent actions, touched files, verification | Full chat history, unrelated rules, stale evidence |

## Audit questions

- Is the reader and trigger explicit at the POU?
- Can the reader act without cold history or an implicit convention?
- Are authority and lifetime single-sourced where values can diverge?
- Is each non-automatic target reachable from a real runtime ingress?
- Are there orphan targets, duplicate authority, cycles, stale edges, or silent fallbacks?
- Did the session load context at the POU, or rely on memory?
- Did a skill, plan, or handoff trigger fire from evidence rather than name association?
- Is missing context blocking action, or is the agent over-reading to feel safer?

## Mechanical vs. LLM judgment

Prefer mechanical checks for file existence, required fields, line limits,
forbidden live tokens, parser drift, schema coverage, hashes, fixture outcomes,
and route-state consistency. Leave LLM judgment for semantic sufficiency,
ownership ambiguity, product meaning, public copy, medical/evidence wording,
and whether a packet would mislead a fresh reader. When a rule is crisp enough
to test twice, recommend promoting it to a checker.

## Output contract

Return only:

```text
Verdict: minimal | under-context | over-context | stale-context | wrong-reader | drifted | wrong-trigger
Reader/trigger:
Required packet:
Drop:
Fresh-read needed:
Mechanical guard:
LLM judgment:
Smallest next action:
```

Keep findings grounded in file paths, line numbers, commands, or exact packet
fields when available. Do not rewrite the packet unless asked.
