---
name: context-novelist
description: |
  Audit and design minimal sufficient context packets with progressive disclosure. A context novelist lives as the next reader of a context packet, not as the author: it walks the reader's first decision at the point of use and reports where the packet fails.
  Use when the user explicitly asks whether a prompt, handoff, AGENTS.md, SKILL.md, lane header, plan, review packet, or multi-agent/context workflow gives too much, too little, stale, or wrongly routed context; when they ask whether a live session is following intent or what upstream context is shaping it; when they mention MSC-PD, minimal sufficient context, progressive disclosure, fresh-context review, or context novelist.
  Do not use this as the generic "novelist" reviewer for spec or implementation narrative dry-runs; those are the `spec-novelist` and `impl-novelist` agents.
---

# Context Novelist

Use this skill as a fresh-context audit lens. A context novelist lives as the next reader of a context packet, not as the author. It walks the reader's first decision at the point of use and reports where the packet fails.

Decide the smallest context packet that lets a future agent do the next task safely, without inheriting stale narrative or evidence dumps.

This is a skill, not a replacement for the narrative novelist agents. For
independent review, spawn the subagent with `fork_turns="none"`, then send this
skill and only the proposed packet or target files. Never use `all` or a recent
turn count; the agent cannot discard inherited conversation after spawning.

When an SDD owner must run both narrative and context checks, dispatch this in parallel with the stage-specific novelist:
- spec stage: `spec-novelist` agent + `context-novelist` skill/agent.
- implementation-final stage: `impl-novelist` agent + `context-novelist` skill/agent only when the final handoff/review packet itself is in scope.

Never let `context-novelist` satisfy or skip a required `spec-novelist` or `impl-novelist` gate.

## Core Rule

Read route-first, then point-of-use.

1. Identify the next decision or task.
2. Name the reader and trigger.
3. Load only routing files first: `AGENTS.md`, index/map, lane live header, handoff, or skill frontmatter.
4. Load contracts, schemas, tests, artifacts, or evidence only when the current task requires them.
5. Do not read History, archives, long evidence, or prior conclusions unless stale-state or provenance is the target.

## Case Packets

Use the smallest matching packet. If several apply, start with the narrowest packet and add only named dependencies.

| Case | Include | Exclude by default |
|---|---|---|
| Code change | User goal, touched files, nearest `AGENTS.md`, relevant tests/checkers, named contract/schema | Whole repo docs, old plans, unrelated dirty files |
| Spec or plan | Approved spec/plan, acceptance criteria, directly named ADRs/contracts, open decisions | All ADRs, full chat history, implementation logs |
| Lane/orchestration | Relevant lane live header before History, `programs.md` active block, named checker/contract, current call if any | Lane History, evidence logs, consumed calls |
| External/fresh review | Objective, exact files/excerpts, audit questions, output contract, forbidden assumptions | Your prior conclusion, intended fix, broad repo dump |
| Evidence/data | Schema, manifest/hash, aggregate counts, failing examples, source authority | Full raw corpus unless sampling/provenance audit requires it |
| UI/design | Target URL or screenshots, design-system entrypoint, current component files, acceptance criteria | Old mock archives, unrelated design variants |
| AGENTS/SKILL/knowledge | Target file, consumer trigger, point-of-use path, duplication/staleness checks | Mirror docs, long explanations of process history |
| Runtime/session audit | User's current intent, injected routing context, explicitly loaded AGENTS/SKILL/handoff/plan/todo, recent tool actions, touched files, declared verification | Full chat history, unrelated global rules, old plans, stale evidence logs |

## Audit Questions

- Is the reader explicit?
- Is the trigger explicit?
- Can the reader act without reading cold history?
- Are break-if-duplicated values single-sourced?
- Is evidence stored outside the hot path?
- Are stale or superseded artifacts clearly cold, deleted, or promoted?
- Can a deterministic checker replace an LLM instruction?
- Did the session load context at the point of use, or rely on memory?
- Which upstream instruction explains the current action?
- Is the session following the user's current intent, or an older inferred goal?
- Did a skill, plan, or handoff trigger fire from evidence, or from name association?
- Is missing context blocking action, or is the agent over-reading to feel safer?

## Mechanical vs LLM

Prefer mechanical checks for file existence, required fields, line limits, forbidden live tokens, parser drift, schema coverage, hashes, fixture outcomes, and route-state consistency.

Leave LLM judgment for semantic sufficiency, ownership ambiguity, product meaning, public copy, medical/evidence wording, and whether a packet would mislead a fresh reader.

When a rule is crisp enough to test twice, recommend promoting it to a checker.

## Output Contract

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

Keep findings grounded in file paths, line numbers, commands, or exact packet fields when available. Do not rewrite the packet unless asked.
