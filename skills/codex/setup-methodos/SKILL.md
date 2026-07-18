---
name: setup-methodos
description: Bootstrap Methodos profiles and runtime roots for a repository when the user asks to set up, adopt, install, wire, configure, or evaluate Methodos.
---

# Setup Methodos

Configure a target repository without treating this skill as an installer.
Apply changes only when the user asks to apply them.

## Setup packet

Record the selected profile, target runtime (Codex, Claude, or both), context
surfaces, skills/agents to copy, hook registration decision, and unresolved
questions. This is planning text only; do not create an evidence artifact.

## Profiles

| Profile | Contents |
|---|---|
| `bootstrap` | `setup-methodos` |
| `core` | `using-methodos`, `grill-me`, `plan`, `impl`, `decision`, `impl-novelist` |
| `core+novelists` | `core` plus `spec-novelist` for multi-flow or multi-actor work |
| `continuity` | `handoff`, `snapshot`, `todo`, `context-novelist` |
| `learning-loop` | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` |
| `optional` | `conditional-heartbeat`, `ask-chatgpt-pro`, `report-kit` |
| `hooks` | reviewed hook scripts plus runtime-specific registration |

`impl` directly closes a simple, low-risk change. For larger work, use the
normal plan/owner routing available in the active runtime; do not assume that a
specific model, effort, transport, or reviewer is proof of completion. A final
review is conditional on real risk predicates, not profile membership.

## Decisions

1. Codex uses `skills/codex/*`; Claude uses `skills/claude/*` and
   `agents/claude/*` when global agents are supported.
2. Choose shared or separated runtime roots explicitly. Shared roots are useful
   when both runtimes edit one project; otherwise use each runtime's defaults.
3. Prefer `AGENTS.md` for Codex and `CLAUDE.md` for Claude. Keep the context
   block short and name only paths that the runtime actually reads.
4. Hooks are inactive until registered and trusted. Never register them by
   surprise.

## Context snippet

```markdown
## Methodos

Profiles: <core | core+novelists | continuity | learning-loop | optional | hooks>
Runtime roots:
- plan_root: <path>
- verify_root: <path>
- todo_root: <path>
- diagnose_root: <path>

Use local tests and exact changed paths for routine work. Select semantic review
only for new public/user flows, shared contracts or permissions/data, external
state/concurrency/migration, or a real integration seam.
```

## Stop conditions

Ask before applying setup when existing runtime files conflict, shared roots are
undecided, hook registration would run code outside the target repository, or
the user wants a reference copy rather than an active setup.
