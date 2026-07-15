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

Dispatch 직전 nearest `AGENTS.md`가 지시한 project machine route가 있으면 그 파일을
point-of-use로 다시 읽는다. 단, 외부 ChatGPT Pro 또는 Claude Fable/Opus route는
현재 사용자가 그 검토에 명시적으로 요청했을 때만 쓴다. 프로젝트 route만으로 외부
reviewer를 자동 호출하지 않는다. 프로젝트 route가 없으면 아래 Codex route를 쓴다.
full reviewer는 현재 부모 세션의 model과 reasoning effort를 상속하고, scoped
reviewer만 낮춘 고정 profile을 쓴다. 이전 reviewer의 값을 상속하지 않는다.

| Gate | Scope | Primary | Model | Effort |
|---|---|---|---|---|
| plan-verify | full | fresh local `plan-verify-reviewer` subagent | parent session 상속 | parent session 상속 |
| plan-verify | scoped | fresh local `plan-verify-scoped-reviewer` subagent | `gpt-5.6-sol` | `medium` |
| impl-verify | full | fresh local `impl-verify-reviewer` subagent | parent session 상속 | parent session 상속 |
| impl-verify | scoped | fresh local `impl-verify-scoped-reviewer` subagent | `gpt-5.6-sol` | `medium` |
| impl-novelist | full | fresh local `impl-novelist` subagent | parent session 상속 | parent session 상속 |
| impl-novelist | scoped | fresh local `impl-novelist-scoped-reviewer` subagent | `gpt-5.6-sol` | `medium` |

Full review는 canonical reviewer prompt, candidate refs, 필요한 파일과 fresh machine
evidence를 self-contained context packet으로 보낸다. full custom-agent TOML은
`model`과 `model_reasoning_effort`를 선언하지 않는다. Codex가 두 값을 부모 세션에서
상속하므로 사용자가 부모 세션을 xhigh로 선택하면 full reviewer도 xhigh다. Packet이
canonical evidence/impact 요구를 판정하기에 부족하거나 reviewer를 실행할 수 없으면
verdict를 추측하거나 외부 provider로 fallback하지 말고 `NEEDS_CONTEXT`로 닫는다.
상속 동작의 upstream 근거는 Codex 공식 [Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)다.

사용자가 외부 Pro/Claude 검토를 명시적으로 요청하면 해당 provider skill/runtime의
session·model·finality 계약을 point-of-use로 읽고 별도 fresh review로 실행한다. 이
명시적 외부 검토 실패도 다른 외부 provider의 자동 호출 사유가 아니다.

Artifact에는 실제 실행 경로의 `reviewer_provider`, `reviewer_transport`,
`reviewer_model`, `reviewer_reasoning_effort`, `reviewer_session_id`,
`fallback_reason`을 기록한다. `fallback_reason`은 shared schema 호환을 위해
유지하지만 자동 fallback이 없는 Codex route에서는 null이다. 기본 local route의 provider/transport는
`codex_local`/`subagent`, session id와 fallback reason은 null이다. local full의
model/effort는 runtime이 실제 값을 노출하면 그 값을 기록하고, 노출하지 않으면 각각
`inherited_from_parent`를 기록한다. 이 값은 unknown이 아니라 custom-agent 설정을
생략해 부모 세션에서 상속했다는 명시적 provenance다. 명시적으로 요청한 외부 검토는
실제 provider/transport/model/effort/session을 기록한다.

Scoped reviewer가 실행 중 exact full-escalation predicate를 발견한 경우 그
`NEEDS_CONTEXT` 응답은 terminal attempt artifact가 아니라 routing envelope다. 같은
attempt/candidate/parent를 유지해 full route로 즉시 재dispatch하고, full 결과만
attempt artifact로 저장한다. 다른 `NEEDS_CONTEXT`는 terminal 결과로 저장한다.

모든 local profile은 `sandbox_mode = "read-only"`를 명시한다. attempt 1은 lineage의
baseline full review이고, BLOCKED/BROKEN fix 뒤 attempt M+1은 scoped가 기본이다.
full 재검증은 owner contract의 explicit escalation predicate가 있을 때만 위 full
local route로 보낸다.
