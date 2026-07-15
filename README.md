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
| Claude skills and agents | Usable reference in `skills/claude/` and `agents/claude/` |
| Codex skills | Usable reference in `skills/codex/` |
| Codex hooks | Reference scripts with `hooks/codex/hooks.example.json`; inactive until registered and trusted |
| Installer | Not provided |
| Public ADR archive | Not included |

The private ADR/research archive is not part of this public package. The runtime
contract and usable harness assets live here.

## Install Profiles

Use these profiles as the stable pick-list when adopting Methodos into another
agent runtime. They are profiles, not installer commands.

| Profile | Start With | Add When |
|---|---|---|
| `bootstrap` | `setup-methodos` | First adoption pass for a repository |
| `core` | Codex: `using-methodos`, `grill-me`, `plan`, `impl`, `decision`, `impl-novelist`; Claude: add `plan-verify`, `impl-verify` | Any non-trivial Methodos workflow |
| `core+novelists` | `core` plus `spec-novelist` and runtime reviewer/novelist agents | Multi-actor or multi-flow feature work |
| `continuity` | `handoff`, `snapshot`, `todo`, `context-novelist` | Long-running work across sessions, compaction, or context surfaces |
| `learning-loop` | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` | Turning repeated confusion or stale artifacts into structural improvements |
| `optional` | `conditional-heartbeat`, `ask-chatgpt-pro`, `report-kit` | Heartbeat wakeups, external second opinion, or HTML lifecycle reporting |
| `hooks` | `hooks/common/*`, `hooks/claude/*`, `hooks/codex/hooks.example.json` | Runtime guardrails after manual review and trust |

For Codex, choose from `skills/codex/`. For Claude, choose from
`skills/claude/` and add `agents/claude/` when isolated agents are available.

## Why

AI coding gets blurry when the model jumps straight from a vague request to
code. Methodos puts durable checkpoints between those steps:

- intent becomes a written spec
- the spec becomes vertical implementation slices
- Claude can verify each plan/slice; Codex consolidates fresh verification at the final candidate
- fresh-context novelist lenses walk lived-use stories before and after implementation
- completion requires evidence artifacts, not just confident prose
- runtime guards catch mismatches between agent prose, tool calls, evidence, and context placement
- runtime-specific wording and hooks may vary, while artifact contracts stay
  stable

## Walkthrough

```text
Idea
  -> grill-me writes docs/specs/<slug>.md
  -> plan writes <plan_root>/<slug>.md
  -> optional high-risk decision-reviewer runs once
  -> impl commits one slice at a time with WHY: and local checks
  -> Codex impl-novelist runs one full final technical+narrative review
  -> failed-review repairs alone receive scoped final reverify
```

The shared contract for these artifacts lives in
[`contract/SKILL-ARTIFACTS.md`](contract/SKILL-ARTIFACTS.md). Runtime-specific
wording, hooks, and agent formats may differ as long as they obey that contract.

## Three Pressures

Methodos does not rely on agent prose alone. It applies three kinds of pressure:

| Pressure | Question | Examples |
|---|---|---|
| Reviewer gates | Is the consequential decision or final candidate correct and evidenced? | conditional `decision-reviewer`, Codex final `impl-novelist`, Claude `plan-verify`/`impl-verify` |
| Novelist lenses | Can the intended actor actually live through the story? | `spec-novelist`, `impl-novelist`, `context-novelist` |
| Runtime guards | Did the runtime actually follow the stated intent? | model gates, evidence wording checks, context-surface guard |

`context-novelist` is part of the novelist family, but it reviews the next
reader's context rather than a product user's feature story. Hooks can suggest
that a context-novelist pass is needed; they do not replace that judgment.

## Runtime Skill Realizations

The artifact contract is shared, but the skill prose is not forced to be
byte-identical across runtimes.

- Claude realizations live in `skills/claude/<skill>/SKILL.md`.
- Codex realizations live in `skills/codex/<skill>/SKILL.md`.
- Claude reviewer and novelist agent prompts live in `agents/claude/`.
- Codex reviewer/novelist skills live in `skills/codex/`; stable read-only
  custom-agent profiles live in `agents/codex/`.

## Skill Families

### Core Gates

| Skill | Role | Artifact |
|---|---|---|
| `setup-methodos` | Repository bootstrap: choose profiles, roots, context surfaces, hooks, and agent wiring | setup packet or context patch |
| `using-methodos` | Passive orientation meta-skill, not a router | none |
| `grill-me` | Intent alignment interview before non-trivial work | `docs/specs/<slug>.md` |
| `plan` | Approved spec to vertical implementation slices | `<plan_root>/<slug>.md` |
| `plan-verify` | Claude isolated adversarial plan review; not an automatic Codex gate | `<verify_root>/plan-*.json` |
| `impl` | Slice implementation with `WHY:` commits | git commits |
| `impl-verify` | Claude isolated slice verification; not an automatic Codex gate | `<verify_root>/slice-*.json` |
| `spec-novelist` | Fresh-context spec lived-use lens | Codex router skill or Claude agent fold |
| `impl-novelist` | Claude lived-use lens; Codex single final technical+narrative verifier | narrative verify report |

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
| `conditional-heartbeat` | Create one-shot Codex heartbeat wakeups with fallback and condition-based acceleration |
| `ask-chatgpt-pro` | Delegate second-opinion review to a logged-in ChatGPT Pro browser session |
| `report-kit` | Produce self-contained lifecycle/status/decision HTML reports |

### Runtime Guards

These are reference hook scripts, not active policy. Codex has a lifecycle hook
system, and this repository includes `hooks/codex/hooks.example.json` as the
registration shape. A runtime must still copy/adapt that file, register the
hooks, and trust them before they run.

The guards are intentionally narrower than the skills: each one catches a
mechanical runtime mismatch and leaves semantic judgment to the relevant
Methodos gate or novelist lens.

| Hook | Role |
|---|---|
| `hooks/claude/delegation-enforcer.py` | Keep Claude agent model intent aligned with the actual Agent tool call |
| `hooks/common/evidence_check.py` | Warn when verify reports use hedged language instead of evidence |
| `hooks/codex/codex-spawn-model-gate.py` | Require explicit model intent on Codex spawned-agent calls |
| `hooks/common/context_surface_guard.py` | Flag suspicious hot-context edits and suggest `context-novelist` review |

## Repository Layout

```text
contract/              Shared artifact schemas and Methodos reference contract
skills/claude/         Claude skill realizations
skills/codex/          Codex skill realizations
agents/claude/         Claude reviewer and novelist agent definitions
hooks/common/          Reference hook scripts usable across runtimes
hooks/claude/          Claude-only hook scripts
hooks/codex/           Codex-only hook scripts and hooks.example.json
runtime-notes/codex.md Codex runtime notes
```

## Adoption

This repository intentionally leaves installation to the adopting runtime or AI
agent. A practical adoption pass usually means:

1. Read `contract/SKILL-ARTIFACTS.md`.
2. Run or follow `setup-methodos` to choose profiles, artifact roots, context
   surfaces, hook registration, and agent/subagent wiring for the target repo.
3. Choose the relevant runtime realization: `skills/claude/*/SKILL.md` for
   Claude or `skills/codex/*/SKILL.md` for Codex. Start with core gates and
   `decision`; add continuity, learning-loop, and extension skills as needed.
4. Adapt reviewer/novelist agents only if the runtime supports isolated agents.
5. Treat `hooks/*` as reference scripts, not automatically installed policy.
   For Codex, start from `hooks/codex/hooks.example.json`: copy/adapt it into
   `~/.codex/hooks.json`, `<repo>/.codex/hooks.json`, inline `[hooks]` in
   `config.toml`, or a Codex plugin manifest, then review/trust the hook.
6. Keep artifact paths and schemas stable when changing prose or runtime setup.

`hooks/common/context_surface_guard.py` is intentionally mechanical. It can
notice broken references or suspicious hot-context placement, then suggest a
`context-novelist` pass; it does not run a model or replace that judgment.

Codex hook support is not the uncertain part; activation is. The scripts here
remain disabled/reference until a runtime registers and trusts them. No
installer is provided.

## Contract Boundary

Shared across runtimes:

- gate names
- artifact paths
- artifact schema fields
- status/tier values that downstream gates read

Free to diverge per runtime:

- runtime-specific `SKILL.md` prose and examples
- hook registration mechanics
- agent/subagent formats
- runtime-specific FORCE devices

If a runtime-specific realization cannot follow the existing skill prose without
causing procedural failure, add a runtime-specific realization and keep the
contract stable.

## License

MIT. See [`LICENSE`](LICENSE).
