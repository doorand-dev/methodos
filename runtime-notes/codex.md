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
- `../agents/claude/*.md`: cross-runtime source prompts. Codex의 stable custom-agent 정본은 `../agents/codex/*.toml`이다.
- Prefer `../skills/codex/*` for Codex sessions. Treat `../skills/claude/*` as the Claude realization, not as the Codex source of truth.

## Reviewer routes

Dispatch 직전 nearest `AGENTS.md`가 지시한 project machine route가 있으면 그 파일을 point-of-use로 다시 읽고 model과 reasoning effort를 둘 다 명시한다. route가 없으면 아래 runtime-local profile을 쓴다. 이전 reviewer/controller의 값이나 Codex runtime default를 상속하지 않는다.

| Gate | Scope | Profile | Model | Effort |
|---|---|---|---|---|
| plan-verify | full | `plan-verify-reviewer` | `gpt-5.6-sol` | `xhigh` |
| plan-verify | scoped | `plan-verify-scoped-reviewer` | `gpt-5.6-sol` | `medium` |
| impl-verify | full | `impl-verify-reviewer` | `gpt-5.6-sol` | `xhigh` |
| impl-verify | scoped | `impl-verify-scoped-reviewer` | `gpt-5.6-sol` | `medium` |
| impl-novelist | full | `impl-novelist` | `gpt-5.6-sol` | `xhigh` |
| impl-novelist | scoped | `impl-novelist-scoped-reviewer` | `gpt-5.6-sol` | `medium` |

모든 profile은 `sandbox_mode = "read-only"`를 명시한다. attempt 1은 lineage의 baseline full review이고, BLOCKED/BROKEN fix 뒤 attempt M+1은 scoped가 기본이다. full 재검증은 owner contract의 explicit escalation predicate가 있을 때만 full profile로 보낸다.
