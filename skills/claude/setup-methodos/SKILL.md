---
name: setup-methodos
description: Bootstrap Methodos profiles and runtime roots for a Claude repository when setup or adoption is requested.
---

# Setup Methodos

Choose the runtime, profiles, context surfaces, skills/agents, hook registration,
and runtime roots. Apply changes only when requested. Keep the setup packet as
conversation text; no evidence schema or attestation is needed.

Profiles are `bootstrap`, `core`, `core+novelists`, `continuity`,
`learning-loop`, `optional`, and `hooks`. `core` includes `grill-me`, `plan`,
`impl`, `decision`, and conditional `impl-novelist`; add `spec-novelist` for
multi-flow work. Routine work closes with tests and exact changed paths; a
semantic final review is selected only for new public/user flows, shared
contracts or permissions/data, external state/concurrency/migration, or a real
integration seam.

Use `CLAUDE.md` for Claude context and `agents/claude/*` for Claude agents.
Hooks remain inactive until explicitly registered and trusted. Ask before
changing conflicting roots or registering code outside the target repository.
