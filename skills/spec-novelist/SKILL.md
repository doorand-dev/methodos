---
name: spec-novelist
description: Route explicit requests for spec novelist, spec narrative dry-run, naive-user spec review, or "스펙 노벨리스트" to the Methodos fresh-context spec-novelist agent. Use when the user asks to run, invoke, review with, or explain spec-novelist outside the grill-me gate. This is a thin discovery/router skill, not the canonical agent prompt; do not use it for context-novelist or implementation-final narrative review.
---

# Spec Novelist

Use this skill to make the name `spec-novelist` discoverable in ordinary Codex sessions.

Do not replace the Methodos agent prompt with this file. The canonical spec novelist realization is:

`agents/claude/spec-novelist.md`

## Procedure

1. Locate the target spec or ask for the spec paste if none is available.
2. Prefer a fresh-context, read-only invocation using the canonical agent prompt.
3. Pass only the spec content required by that prompt. Do not pass main-session intent history.
4. Require raw JSON output in the canonical shape from the agent prompt.
5. If fresh-context invocation is unavailable, say that the run is degraded and perform a read-only manual pass from the same stance. Do not claim it satisfies a Methodos gate unless the gate's artifact requirements are met.

## Boundaries

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `impl-novelist` for final assembled implementation narrative review.
- Do not copy agent prompt details into this skill. Read the canonical agent prompt at point of use.
