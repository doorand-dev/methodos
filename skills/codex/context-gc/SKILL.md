---
name: context-gc
description: |
  Run a scoped or full mark-and-sweep audit of context contracts, documentation procedures, runtime ingresses, hooks, skills, AGENTS files, handoffs, plans, maps, indexes, and their consumers. Include incidents from the workspace-local .Codex/context-friction.md when present, but do not require incidents. Use when the user explicitly says "context gc", "context-gc", "/context-gc", "컨텍스트 GC", "컨텍스트 전수 조사", asks to audit a named scope for stale context contracts or procedures, or asks whether documented workflow still matches runtime reality. Do not trigger from generic "gc", cleanup, documentation review, a single packet review, or a local routing edit.
---

# Context GC

Audit whether the existing context system is live, reachable, truthful, and
properly retained. This is a garbage collector for context contracts, not only
a backlog processor and not an architecture invention skill.

## Modes and scope

Resolve exactly one scope before reading deeply:

| Invocation | Scope |
|---|---|
| `/context-gc <path-or-artifact>` | Named file, subtree, skill, hook, workflow, or contract |
| `/context-gc --ingress <trigger>` | Graph reachable from one real runtime ingress |
| `/context-gc --incidents` | All entries in `.Codex/context-friction.md`; prioritize open and uncertain |
| `/context-gc --full` | Current workspace plus only global contracts actually connected to it |
| bare `/context-gc` | Current workspace |

Do not cross into another repository or unrelated global surface unless the
user names it or a marked edge from the current scope reaches it.

## Mark-and-sweep audit

### 1. Discover roots and inventory

Start from real runtime ingresses: AGENTS discovery, skill metadata and explicit
invocation, hook events, commands, agent or job entrypoints, resolvers, maps,
indexes, and declared plan or handoff consumers. Use `rg --files` and focused
configuration reads to inventory metadata before opening file bodies.

Treat `.Codex/context-friction.md` as a hint and evidence source, never as the
complete inventory. Its absence does not imply a clean context system.
When the store exists, report the classification distribution and
`context-fault: yes | no | uncertain` ratios across all entries. Then inspect
open and uncertain entries as sweep candidates. This keeps `no` incidents live
as an escape-valve signal without sending closed incidents into architecture
processing.

### 2. Mark reachable context

Walk only evidenced edges and record each one as:

```text
From | Trigger | Action | To | Lifetime | Authority | Failure
```

Distinguish automatic ingress from explicit user action and undocumented model
convention. A file that exists but has no real trigger is not marked live.

### 3. Validate liveness and truth

Reachability alone is insufficient. For every marked contract, test the
smallest applicable signals:

- referenced paths, commands, schemas, and hook events still exist;
- the declared trigger can reach the named consumer and point of use;
- procedure steps match current code, configuration, and runtime behavior;
- authority has not moved to another source;
- lifetime has not ended;
- the packet is required by its reader rather than retained by habit;
- failure behavior is explicit rather than a silent fallback.

Prefer mechanical checks for existence, parsers, schema fields, route state,
and executable commands. Use semantic judgment for procedural truth,
duplication, authority, and reader sufficiency.

### 4. Classify garbage

Use exactly one primary class per candidate:

| Class | Meaning |
|---|---|
| `unreachable` | No real ingress reaches the target |
| `dangling` | A reference points to a missing target |
| `dead-trigger` | The declared trigger no longer occurs |
| `expired` | The artifact outlived its declared lifecycle |
| `superseded` | A newer authority replaced it |
| `shadowed` | Lower authority still presents itself as canonical |
| `contradictory` | Contract and implementation or two authorities disagree |
| `duplicate` | The same decision is owned in multiple places |
| `misplaced` | Context is injected at the wrong scope or reader |
| `over-retained` | Context survives longer than its useful lifetime |
| `over-loaded` | A point of use receives unnecessary context |
| `unverifiable` | Consumer, trigger, authority, or reality check is unavailable |

Do not equate `unused` with garbage. A manual human reference can be live even
when no runtime injects it; record its actual reader and trigger.

### 5. Sweep proposal

Remain read-only unless the user explicitly authorizes cleanup. For each
candidate recommend one of `delete`, `update`, `move`, `deduplicate`,
`reconnect`, `shorten-lifetime`, `reduce-packet`, `keep`, or
`escalate-architecture`.

Exact repair of an evidenced stale contract can proceed through the normal
implementation gate. A new resolver, authority model, hook topology, loading
layer, or composition belongs to `improve-context-architecture`.

## Output

Return the audit in this compact form; do not create a report file unless the
user asks:

```text
Verdict: clean | garbage-found | drifted | unverifiable
Scope:
Roots:
Marked nodes/edges:
Incident hints used:
Incident distribution/fault ratio:
Candidates: <class | evidence | reader/trigger | proposed sweep>
Architecture escalations:
Smallest next action:
```

Every candidate must cite a path and line, exact field, command result, or
runtime event. A broad claim without one of these is not a sweep candidate.

## Companion routing

- `blame-context` appends immediate incidents to the dedicated store.
- `context-novelist` owns focused packet and point-of-use sufficiency audits.
- `improve-context-architecture` owns structural deepening after this audit
  shows a repeated or system-level limitation.
