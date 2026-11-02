---
name: ai-knowledge-routing
description: |
  Use when the user mentions "전역 지식" or "AI 지식", or asks to read,
  search, store, route, or decide whether knowledge belongs in the global AI
  knowledge base, including source extraction, provenance, retrieval, RAG, or
  agent memory.
---

# AI Knowledge Routing

`<knowledge-root>` is an adopter-chosen knowledge repository declared in the project AGENTS.md. Configure it before using global lookup; never assume a personal filesystem path.

Route only. Do not store sources, promote claims, or build automation here.

## Flow

```text
user material
→ goal / input / transform / output / verify
→ destination
→ consumer path
→ delegated skill or no artifact
```

## Destination

```text
project-specific + local reader → current repo path
reusable AI-system knowledge → <knowledge-root>
raw source / link / thread / claims → provenance first
repeatable process failure → automation/checker/trace/eval
no future reader or trigger → no artifact
```

## This Repo

```text
source material → digest
supported reusable knowledge → promote
best decision question → decide
what do we know? → ask
route/schema/citation drift → audit
```

Read `index.md` first, then only the routed page.

Use its "지식 기록 경계" section to distinguish reusable AI knowledge, project-local findings (external behavior, failed approaches, workarounds), and Skills/FACTS (source-verified skill/harness facts with path:line + SHA). Keep project evidence at its owning destination.

The discontinued LLM Wiki folder is not a lookup or storage destination. Do not fall back to it when searches miss. Preserve historical evidence and ai-knowledge concept/source references; these do not reactivate that folder. Archiving, moving, or deleting the folder requires separate user confirmation.

## Named Entity and Alias Lookup

When a topic router does not select one unambiguous first-read page, or the user names a specific tool, repo, product, model, provider, source id, project, or phrase such as `AgentSpace`, `Lightpanda`, `RTK`, `저가모델 cascading`, or `NVIDIA cascade`, do not invent a new topic-index row first.

1. Search the current project first for that exact name and obvious aliases.
2. If the project has no local hit, search `<knowledge-root>` claimset frontmatter `aliases` before broader files. `aliases` is exact retrieval metadata; `topics` is stable classification metadata.
3. If no alias matches, search `index.md`, `indexes/`, `claimsets/`, `digests/`, `sources/`, and `extracts/` for the term and obvious variants.
4. If found globally but not locally, say: project-local docs are missing, but global ai-knowledge has this entity; then route to the found claimset/digest/source.
5. Only say "not found" after both local project lookup and global entity lookup fail.

## Other Repos

```text
AGENTS / index / lane / map / handoff / SKILL
→ local consumer exists? edit that path
→ no consumer? ask or state missing reader
→ reusable lesson? route to <knowledge-root>
```

## Extraction

```text
raw source ≠ current understanding
digest/extract ≠ truth
claimset = candidate claims
synthesis/concept/playbook = promoted understanding
```

Track authority, freshness, scope, support/conflict, open checks, and recheck trigger only when relevant.

Keep project facts project-scoped.

## Storage

- Reader + trigger required.
- Existing source of truth first.
- Route files route; evidence files carry evidence.
- No orphan docs. No mirror docs.
- Single source for break-if-duplicated values.

## Automation

Concrete failure only:

```text
S1 stable one input/output → script or structured prompt
S2 steps/branches/retries → workflow + saved state
S3 tools/retrieval/evals → RAG/tools/traces/evals
S4 coordination failure → agents/orchestration
```

No failure → no new layer.

## Stop Signs

- Source text treated as truth.
- Project facts promoted as global truth.
- Vector DB, graph, MCP, or agents before failure evidence.
- Detailed evidence or final judgment in index/map/lane files.
