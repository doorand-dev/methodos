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
| Codex support | Experimental wiring notes and hook candidates |
| Installer | Not provided |
| Public ADR archive | Not included |

The private ADR/research archive is not part of this public package. ADR links
inside skill bodies are rationale breadcrumbs from the source workspace; the
runtime contract and usable harness assets live here.

## Why

AI coding gets blurry when the model jumps straight from a vague request to
code. Methodos puts durable checkpoints between those steps:

- intent becomes a written spec
- the spec becomes vertical implementation slices
- each plan and slice gets isolated verification
- completion requires evidence artifacts, not just confident prose
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
wording, hooks, and agent wiring may differ as long as they obey that contract.

## Gates

| Gate | Role | Artifact |
|---|---|---|
| `using-methodos` | Passive orientation meta-skill, not a router | none |
| `grill-me` | Intent alignment interview before non-trivial work | `docs/specs/<slug>.md` |
| `plan` | Approved spec to vertical implementation slices | `.claude/plans/<slug>.md` |
| `plan-verify` | Isolated adversarial plan review | `.claude/verify-reports/plan-*.json` |
| `impl` | Slice implementation with `WHY:` commits | git commits |
| `impl-verify` | Isolated slice verification | `.claude/verify-reports/slice-*.json` |
| `context-novelist` | Minimal sufficient context audit | review judgment |

Additional discovery skills:

- `spec-novelist`: thin Codex-facing router to the spec narrative agent.
- `impl-novelist`: thin Codex-facing router to the final implementation narrative agent.

## Repository Layout

```text
contract/              Shared artifact schemas and Methodos reference contract
skills/                Top-level skills for a runtime to adapt
agents/claude/         Claude reviewer and novelist agent definitions
hooks/common/          Hook candidates usable across runtimes
hooks/claude/          Claude-only hook candidates
hooks/codex/           Codex-only hook candidates
adapters/codex/        Codex wiring notes
```

## Adoption

This repository intentionally leaves installation to the adopting runtime or AI
agent. A practical adoption pass usually means:

1. Read `contract/SKILL-ARTIFACTS.md`.
2. Adapt the relevant `skills/*/SKILL.md` files into the runtime's skill format.
3. Adapt reviewer/novelist agents only if the runtime supports isolated agents.
4. Treat `hooks/*` as candidates, not automatically installed policy.
5. Keep artifact paths and schemas stable when changing prose or wiring.

Codex support is experimental. Hook candidates and routing notes are included,
but no stable Codex adapter is provided.

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
