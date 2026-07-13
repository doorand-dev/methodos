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
2. Read the nearest project machine route at point of use. Without one, run the
   full baseline through a fresh `ask-chatgpt-pro(pro/extended)` web session.
   Keep `impl-novelist(gpt-5.6-sol/xhigh)` only as a fresh read-only fallback
   when no review result is obtained because of an allowed transport/finality
   failure. Same-lineage repair attempts use the fresh scoped
   `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)`.
3. Pass the canonical prompt, spec user stories, success criteria, base/head range,
   required source/diff, and fresh machine evidence as a self-contained attachment/
   context packet. Do not pass implementation discussion.
4. Require raw JSON output in the canonical shape from the agent prompt.
5. Treat a final Pro `BROKEN`, `NEEDS_CONTEXT`, or issue-bearing result as a
   successful review; never use its verdict as a fallback reason. Permit local
   full fallback only for `provider_send_failure`,
   `model_or_effort_unconfirmed`, `timeout`, `finality_failure`, or
   `attachment_or_context_failure`, and persist the reason. If both routes fail,
   return `NEEDS_CONTEXT` rather than claiming the gate passed.

## Boundaries

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for spec-stage narrative review before planning.
- Do not copy agent prompt details into this skill. Read the canonical agent prompt at point of use.
