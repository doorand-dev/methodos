---
name: impl-novelist
description: Route explicit requests for impl novelist, implementation novelist, final narrative dry-run, assembled implementation naive-user review, or "구현 노벨리스트" to the Methodos fresh-context impl-novelist agent. Use when the user asks to run, invoke, review with, or explain impl-novelist outside the impl final gate. This is a thin discovery/router skill, not the canonical agent prompt; do not use it for context-novelist or spec narrative review.
---

# Impl Novelist

Use this skill to make the name `impl-novelist` discoverable in ordinary Codex sessions.

Do not replace the Methodos agent prompt with this file. This repository ships
the Claude agent prompt as source material for a Codex subagent adaptation:

`../../../agents/claude/impl-novelist.md`

## Procedure

1. Locate the target spec, implementation range, and repo under review. Ask for missing required inputs instead of inventing them.
2. Read the nearest project machine route at point of use. By default, run the
   full baseline through a fresh read-only `impl-novelist` subagent whose custom
   agent file omits `model` and `model_reasoning_effort`, so both inherit from
   the parent session. Same-lineage repair attempts use the fresh scoped
   `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)`. Use ChatGPT Pro or
   Claude Fable/Opus only when the user explicitly requests that external
   review.
3. Pass the canonical prompt, spec user stories, success criteria, base/head range,
   required source/diff, and fresh machine evidence as a self-contained attachment/
   context packet. Do not pass implementation discussion.
4. Require raw JSON output in the canonical shape from the agent prompt.
5. If the local subagent cannot run or the context packet is insufficient,
   return `NEEDS_CONTEXT`; do not auto-call an external provider. For an
   explicitly requested external review, apply that provider's session/model/
   finality contract and treat its final `BROKEN`, `NEEDS_CONTEXT`, or
   issue-bearing result as a successful review result. Its failure does not
   authorize another provider automatically.

## Boundaries

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for spec-stage narrative review before planning.
- Do not copy agent prompt details into this skill. Read the canonical agent prompt at point of use.
