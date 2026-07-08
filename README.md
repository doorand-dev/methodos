# Methodos

Methodos is a reference harness for AI coding agents: it turns vague ideas into
specs, plans, verified slices, and evidence-backed commits.

It is not a central router and it is not an installer package. Each gate is a
top-level skill that self-triggers when its local conditions are met. Use this
repository as a reference kit: read the contract, inspect the skills, and adapt
the pieces to your own Claude, Codex, or other agent runtime.

## Status

| Area | Status |
|---|---|
| Runtime contract | Stable reference |
| Claude skills and agents | Usable reference |
| Codex support | Experimental runtime notes and hook candidates |
| Installer | Not provided |
| Public ADR archive | Not included |

The private ADR/research archive is not part of this public package. The runtime
contract and usable harness assets live here.

## Why

AI coding gets blurry when the model jumps straight from a vague request to
code. Methodos puts durable checkpoints between those steps:

- intent becomes a written spec
- the spec becomes vertical implementation slices
- each plan and slice gets isolated verification
- fresh-context novelist lenses walk lived-use stories before and after implementation
- completion requires evidence artifacts, not just confident prose
- runtime guards catch mismatches between agent prose, tool calls, evidence, and context placement
- runtime-specific wording and hooks may vary, while artifact contracts stay
  stable

## Walkthrough

```text
Idea
  -> grill-me writes docs/specs/<slug>.md
  -> plan writes .claude/plans/<slug>.md
  -> plan-verify writes .claude/verify-reports/plan-*.json
  -> impl commits one slice at a time with WHY:
  -> impl-verify writes .claude/verify-reports/slice-*.json
  -> impl-novelist walks the assembled result before final confidence
```

The shared contract for these artifacts lives in
[`contract/SKILL-ARTIFACTS.md`](contract/SKILL-ARTIFACTS.md). Runtime-specific
wording, hooks, and agent formats may differ as long as they obey that contract.

## Three Pressures

Methodos does not rely on agent prose alone. It applies three kinds of pressure:

| Pressure | Question | Examples |
|---|---|---|
| Reviewer gates | Is the plan or slice correct, evidenced, and within contract? | `plan-verify`, `impl-verify`, reviewer agents |
| Novelist lenses | Can the intended actor actually live through the story? | `spec-novelist`, `impl-novelist`, `context-novelist` |
| Runtime guards | Did the runtime actually follow the stated intent? | model gates, evidence wording checks, context-surface guard |

`context-novelist` is part of the novelist family, but it reviews the next
reader's context rather than a product user's feature story. Hooks can suggest
that a context-novelist pass is needed; they do not replace that judgment.

## Skill Families

### Core Gates

| Skill | Role | Artifact |
|---|---|---|
| `using-methodos` | Passive orientation meta-skill, not a router | none |
| `grill-me` | Intent alignment interview before non-trivial work | `docs/specs/<slug>.md` |
| `plan` | Approved spec to vertical implementation slices | `.claude/plans/<slug>.md` |
| `plan-verify` | Isolated adversarial plan review | `.claude/verify-reports/plan-*.json` |
| `impl` | Slice implementation with `WHY:` commits | git commits |
| `impl-verify` | Isolated slice verification | `.claude/verify-reports/slice-*.json` |
| `spec-novelist` | Fresh-context spec lived-use lens | spec fold |
| `impl-novelist` | Final assembled implementation lived-use lens | `.claude/verify-reports/narrative-*.json` |

### Governance

`decision` is not a gate, but it is core Methodos governance. It handles option
comparison, irreversible changes, temporary patches, and FORCE/OPEN judgment.

### Continuity

| Skill | Role |
|---|---|
| `handoff` | Task-scoped next-session context packet |
| `snapshot` | Same-session pre-compact priority snapshot |
| `todo` | Project-persistent task list |
| `context-novelist` | Minimal sufficient context audit for prompts, handoffs, plans, and runtime context |

### Learning Loop

| Skill | Role |
|---|---|
| `blame-code` | Turn AI confusion into code/documentation friction records |
| `finding` | Preserve external-system facts and failed paths that code cannot encode |
| `gc` | Surface stale artifacts, friction backlog, dead code, duplicates, and context drift |
| `improve-codebase-architecture` | Convert accumulated friction into deeper modules and better seams |

### Optional Extensions

| Skill | Role |
|---|---|
| `ask-chatgpt-pro` | Delegate second-opinion review to a logged-in ChatGPT Pro browser session |
| `report-kit` | Produce self-contained lifecycle/status/decision HTML reports |

### Runtime Guards

These are hook candidates, not installed policy. They are intentionally narrower
than the skills: each guard catches a mechanical runtime mismatch and leaves
semantic judgment to the relevant Methodos gate or novelist lens.

| Hook | Role |
|---|---|
| `hooks/claude/delegation-enforcer.py` | Keep Claude agent model intent aligned with the actual Agent tool call |
| `hooks/common/evidence_check.py` | Warn when verify reports use hedged language instead of evidence |
| `hooks/codex/codex-spawn-model-gate.py` | Require explicit model intent on Codex spawned-agent calls |
| `hooks/common/context_surface_guard.py` | Flag suspicious hot-context edits and suggest `context-novelist` review |

## Repository Layout

```text
contract/              Shared artifact schemas and Methodos reference contract
skills/                Core gates, governance, continuity, learning-loop, and extension skills
agents/claude/         Claude reviewer and novelist agent definitions
hooks/common/          Hook candidates usable across runtimes
hooks/claude/          Claude-only hook candidates
hooks/codex/           Codex-only hook candidates
runtime-notes/codex.md Codex runtime notes
```

## Adoption

This repository intentionally leaves installation to the adopting runtime or AI
agent. A practical adoption pass usually means:

1. Read `contract/SKILL-ARTIFACTS.md`.
2. Adapt the relevant `skills/*/SKILL.md` files into the runtime's skill format.
   Start with core gates and `decision`; add continuity, learning-loop, and
   extension skills as needed.
3. Adapt reviewer/novelist agents only if the runtime supports isolated agents.
4. Treat `hooks/*` as candidates, not automatically installed policy.
5. Keep artifact paths and schemas stable when changing prose or runtime setup.

`hooks/common/context_surface_guard.py` is intentionally mechanical. It can
notice broken references or suspicious hot-context placement, then suggest a
`context-novelist` pass; it does not run a model or replace that judgment.

Codex support is experimental. Hook candidates and runtime notes are included,
but no stable Codex setup is provided.

## Contract Boundary

Shared across runtimes:

- gate names
- artifact paths
- artifact schema fields
- status/tier values that downstream gates read

Free to diverge per runtime:

- `SKILL.md` prose and examples
- hook registration mechanics
- agent/subagent formats
- runtime-specific FORCE devices

If a runtime-specific realization cannot follow the existing skill prose without
causing procedural failure, add a runtime-specific realization and keep the
contract stable.

## License

MIT. See [`LICENSE`](LICENSE).
