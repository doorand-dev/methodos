---
name: setup-methodos
description: Bootstrap Methodos for a repository. Use when the user asks to set up, adopt, install, wire, configure, or evaluate Methodos in a target repo; when another PC or agent needs to decide which Methodos skills to copy; or when artifact roots, AGENTS.md/CLAUDE.md placement, hook registration, or Codex/Claude runtime sharing are unclear. This is an explicit setup skill, not a self-triggering coding gate and not an installer.
---

# Setup Methodos

Configure a target repository to use Methodos without pretending this repository is an installer.

## Output

Produce a setup packet first. Apply file changes only when the user explicitly asks to apply them.

The setup packet must contain:

- selected profile(s)
- target runtime(s): Codex, Claude, or both
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
| `core+novelists` | `core` plus `spec-novelist`, `impl-novelist`; add reviewer/novelist agents when the runtime supports isolated agents |
| `continuity` | `handoff`, `snapshot`, `todo`, `context-novelist` |
| `learning-loop` | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` |
| `optional` | `ask-chatgpt-pro`, `report-kit` |
| `hooks` | reviewed hook scripts plus runtime-specific registration |

Default recommendation: `core`. Add `core+novelists` for multi-file or multi-flow feature work. Add `continuity` for long tasks. Add `hooks` only after the target runtime's hook registration and trust step are clear.

## Decisions

Ask or infer from repo files, but do not silently invent when the answer changes artifact compatibility.

1. Runtime:
   - Codex only: use `skills/codex/*`.
   - Claude only: use `skills/claude/*` and `agents/claude/*` if global agents are available.
   - Both: decide whether artifact roots are shared or separated.

2. Artifact roots:
   - Shared roots: both runtimes read/write the same `plan_root`, `verify_root`, `todo_root`, and `diagnose_root`.
   - Separated roots: Claude defaults to `.claude/*`; Codex defaults to `.Codex/*`.
   - If both runtimes will touch the same project, prefer explicit shared roots in the repo context surface.

3. Context surfaces:
   - Codex: prefer `AGENTS.md`.
   - Claude: prefer `CLAUDE.md`.
   - Both runtimes: write the same artifact root decision in both surfaces, or make one file point to the other only if that runtime actually reads it.

4. Agents:
   - Claude agent prompts live under `agents/claude/`.
   - Codex subagent wiring is runtime-local. If no native subagent role exists, record degraded mode instead of claiming a fresh reviewer gate was satisfied.

5. Hooks:
   - Hook scripts are inactive until registered and trusted.
   - Codex starts from `hooks/codex/hooks.example.json`.
   - Claude uses Claude hook registration, not Codex hook JSON.
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

- the repo already has conflicting `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.Codex/`, or skill folders
- Claude and Codex will co-work but artifact roots are undecided
- hook registration would run code outside the target repo
- the user wants a one-time reference copy rather than active runtime setup
