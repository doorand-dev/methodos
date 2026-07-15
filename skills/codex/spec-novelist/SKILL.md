---
name: spec-novelist
description: Run one lightweight fresh-context narrative pass for a multi-actor or multi-flow spec, or on explicit spec novelist requests. Use the Codex spec-novelist gpt-5.6-sol/medium profile, fold gaps into the existing spec review, and never create a repeat review round. Do not use it for context packets or final implementation verification.
---

# Spec Novelist

Use this skill to make the name `spec-novelist` discoverable in ordinary Codex sessions.

The stable Codex profile is `../../../agents/codex/spec-novelist.toml`. The
Claude prompt remains cross-runtime source material, not the Codex execution route.

## Procedure

1. Locate the target spec or ask for the spec paste if none is available.
2. Use the fresh read-only `spec-novelist(gpt-5.6-sol/medium)` profile.
3. Pass only the spec content required by that prompt. Do not pass main-session intent history.
4. Require raw JSON output in the canonical shape from the agent prompt.
5. Fold gaps once into the spec and continue to its existing user review. Do not
   dispatch a second novelist after the fold.
6. If fresh-context invocation is unavailable, say that the run is degraded and perform a read-only manual pass from the same stance. Do not claim it satisfies a Methodos gate unless the gate's artifact requirements are met.

## Boundaries

- Use `context-novelist` for AGENTS.md, SKILL.md, handoff, review packet, or runtime context audits.
- Use `impl-novelist` for final assembled implementation narrative review.
- Do not copy agent prompt details into this skill. Read the canonical agent prompt at point of use.
