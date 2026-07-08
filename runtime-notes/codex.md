# Codex Runtime Notes

Methodos shares artifact contracts across runtimes. Codex should adapt the
skills, hooks, and agent prompts to its own conventions instead of copying
Claude setup behavior.

- `../hooks/common/evidence_check.py`: candidate for evidence wording checks.
- `../hooks/common/context_surface_guard.py`: candidate for mechanical context-surface checks on `AGENTS.md`, `CLAUDE.md`, and `SKILL.md`; it only advises when `context-novelist` should review semantic placement.
- `../hooks/codex/codex-spawn-model-gate.py`: candidate for requiring explicit model intent on Codex spawned agents.
- `../hooks/claude/delegation-enforcer.py`: Claude-only; do not use directly in Codex.
- `../agents/claude/*.md`: source material for possible Codex subagent prompts; no stable `.toml` definitions live here.
- Create Codex-specific skill prose only where Claude wording would make Codex fail procedurally.
