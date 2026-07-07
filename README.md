# Methodos

Methodos is a distributed AI coding harness. It has no central router: each gate
self-triggers when its local conditions are met.

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

The runtime-shared contract lives in
[`contract/SKILL-ARTIFACTS.md`](contract/SKILL-ARTIFACTS.md). Runtime-specific
wording, hooks, and agent wiring may differ as long as they obey that contract.

The private ADR/research archive is not part of this public package. ADR links
inside skill bodies are rationale breadcrumbs from the source workspace; the
runtime contract and usable harness assets live in this repository.

## Repository Layout

```text
contract/              Shared artifact schemas and Methodos reference contract
skills/                Top-level skills installed into a runtime
agents/claude/         Claude reviewer and novelist agent definitions
hooks/common/          Hook candidates usable across runtimes
hooks/claude/          Claude-only hooks
hooks/codex/           Codex-only hook candidates
adapters/claude/       Claude installer
adapters/codex/        Codex wiring notes
```

## Claude

Preview a local project install:

```powershell
./adapters/claude/setup.ps1 -Local C:\path\to\project -DryRun
```

Install into one project:

```powershell
./adapters/claude/setup.ps1 -Local C:\path\to\project
```

Install globally:

```powershell
./adapters/claude/setup.ps1 -Global
```

Global mode installs skills, reference contract files, Claude agents, and hooks.
Local mode installs only project-local skills and reference contract files.

## Codex

Codex support is intentionally not a line-by-line port of the Claude installer.
See [`adapters/codex/README.md`](adapters/codex/README.md) for the current
wiring notes and hook candidates.

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
