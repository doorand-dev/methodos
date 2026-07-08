---
name: setup-methodos
description: Bootstrap Methodos for a repository. Use when the user asks to set up, adopt, install, wire, configure, or evaluate Methodos in a target repo; when a Claude project needs Methodos profiles, artifact roots, CLAUDE.md placement, hook registration, or reviewer/novelist agent wiring decided. This is an explicit setup skill, not a self-triggering coding gate.
---

# Setup Methodos

Configure a target repository to use Methodos without turning the reference kit into an implicit installer.

## Output

Produce a setup packet first. Apply file changes only when the user explicitly asks to apply them.

The setup packet must contain:

- selected profile(s)
- target runtime(s): Claude, Codex, or both
- artifact root policy
- context surfaces to edit
- skills and agents to copy or adapt
- hook registration decision
- unresolved questions, if any

## Profiles

Use this stable pick-list:

| Profile | Contents |
|---|---|
| `bootstrap` | `setup-methodos` |
| `core` | `using-methodos`, `grill-me`, `plan`, `plan-verify`, `impl`, `impl-verify`, `decision` |
| `core+novelists` | `core` plus `spec-novelist`, `impl-novelist`; add reviewer/novelist agents when isolated agents are available |
| `continuity` | `handoff`, `snapshot`, `todo`, `context-novelist` |
| `learning-loop` | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` |
| `optional` | `ask-chatgpt-pro`, `report-kit` |
| `hooks` | reviewed hook scripts plus Claude hook registration |

Default recommendation: `core`. Add `core+novelists` for multi-file or multi-flow feature work. Add `continuity` for long tasks. Add `hooks` only after hook registration and trust are clear.

## Decisions

1. Runtime:
   - Claude only: use `skills/claude/*` and `agents/claude/*` when global agents are available.
   - Codex only: use `skills/codex/*`.
   - Both: decide whether artifact roots are shared or separated.

2. Artifact roots:
   - Shared roots: both runtimes read/write the same `plan_root`, `verify_root`, `todo_root`, and `diagnose_root`.
   - Separated roots: Claude defaults to `.claude/*`; Codex defaults to `.Codex/*`.
   - If both runtimes will touch the same project, prefer explicit shared roots in both runtime context surfaces.

3. Context surfaces:
   - Claude: prefer `CLAUDE.md`.
   - Codex: prefer `AGENTS.md`.
   - Do not assume one runtime reads the other runtime's context file.

4. Agents:
   - Claude reviewer and novelist prompts live under `agents/claude/`.
   - If agents are not global or not available, record degraded mode instead of claiming a fresh reviewer gate was satisfied.

5. Hooks:
   - Hook scripts are inactive until registered and trusted.
   - Claude hook registration is Claude-specific; do not use Codex hook JSON for Claude.
   - Never register hooks by surprise.

## Context Snippet

When applying setup to a target repo, add a short block like this to the runtime context file and fill the chosen values:

```markdown
## Methodos

Use Methodos for non-trivial AI coding work.

Profiles: <core | core+novelists | continuity | learning-loop | optional | hooks>
Runtime roots:
- plan_root: <path>
- verify_root: <path>
- todo_root: <path>
- diagnose_root: <path>

Runtime notes:
- Gates self-trigger; there is no central router.
- `using-methodos` is orientation only.
- Keep Methodos artifacts tracked except temporary/cache folders.
- Hooks are active only if this repo or the user runtime explicitly registers and trusts them.
```

Keep the block small. Do not paste the whole Methodos README into a hot context file.

## Stop Conditions

Stop and ask before applying setup if:

- the repo already has conflicting `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.Codex/`, or skill folders
- Claude and Codex will co-work but artifact roots are undecided
- hook registration would run code outside the target repo
- the user wants a one-time reference copy rather than active runtime setup
