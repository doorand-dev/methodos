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
2. Prefer a fresh-context, read-only invocation using the canonical agent prompt.
3. Pass only the spec user stories, success criteria, base/head range, and repo location required by that prompt. Do not pass implementation discussion.
4. Require raw JSON output in the canonical shape from the agent prompt.
5. If fresh-context invocation is unavailable, say that the run is degraded and perform a read-only manual pass from the same stance. Do not claim it satisfies a Methodos gate unless the gate's artifact requirements are met.

## Boundaries

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `spec-novelist` for spec-stage narrative review before planning.
- Do not copy agent prompt details into this skill. Read the canonical agent prompt at point of use.
