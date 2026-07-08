# Codex Runtime Notes

Methodos shares artifact contracts across runtimes. Codex should adapt the
skills, hooks, and agent prompts to its own conventions instead of copying
Claude setup behavior.

Codex skill realizations live in `../skills/codex/<skill>/SKILL.md`. They are
not byte copies of the Claude skills; they use Codex-facing context surfaces
such as `AGENTS.md`, Codex skill metadata, and Codex subagent roles where that
is the correct point of use.

Codex lifecycle hooks are a real runtime feature, but the hook files in this
repository are not active by themselves. Start from
`../hooks/codex/hooks.example.json`, then copy/adapt it into the adopting Codex
environment and trust it there. Until then, treat the files below as disabled
reference scripts.

- `../hooks/common/evidence_check.py`: reference script for evidence wording checks.
- `../hooks/common/context_surface_guard.py`: reference script for mechanical context-surface checks on `AGENTS.md`, `CLAUDE.md`, and `SKILL.md`; it only advises when `context-novelist` should review semantic placement.
- `../hooks/codex/codex-spawn-model-gate.py`: reference script for requiring explicit model intent on Codex spawned agents.
- `../hooks/codex/hooks.example.json`: Codex registration example. Copy/adapt it; do not expect Codex to load it under this name.
- `../hooks/claude/delegation-enforcer.py`: Claude-only; do not use directly in Codex.
- `../agents/claude/*.md`: source material for possible Codex subagent prompts; no stable `.toml` definitions live here.
- Prefer `../skills/codex/*` for Codex sessions. Treat `../skills/claude/*` as the Claude realization, not as the Codex source of truth.
