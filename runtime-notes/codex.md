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
point-of-use로 다시 읽고 provider, model, reasoning effort를 모두 명시한다. 프로젝트
route가 없으면 아래 Codex route를 쓴다. 이전 reviewer/controller 값이나 runtime
default를 상속하지 않는다.

| Gate | Scope | Primary | Model | Effort | Local fallback |
|---|---|---|---|---|---|
| plan-verify | full | fresh ChatGPT web session via `ask-chatgpt-pro` | `pro` | `extended` | `plan-verify-reviewer(gpt-5.6-sol/xhigh)` |
| plan-verify | scoped | fresh local subagent | `gpt-5.6-sol` | `medium` | none |
| impl-verify | full | fresh ChatGPT web session via `ask-chatgpt-pro` | `pro` | `extended` | `impl-verify-reviewer(gpt-5.6-sol/xhigh)` |
| impl-verify | scoped | fresh local subagent | `gpt-5.6-sol` | `medium` | none |
| impl-novelist | full | fresh ChatGPT web session via `ask-chatgpt-pro` | `pro` | `extended` | `impl-novelist(gpt-5.6-sol/xhigh)` |
| impl-novelist | scoped | fresh local subagent | `gpt-5.6-sol` | `medium` | none |

Full review는 canonical reviewer prompt, candidate refs, 필요한 파일과 fresh machine
evidence를 self-contained attachment/context packet으로 보낸다. `ask-chatgpt-pro`의
model/effort 확인과 finality gate를 통과한 최종 답만 review 결과다. Pro가
`BLOCKED`, `BROKEN`, `NEEDS_CONTEXT`, 또는 issue를 반환한 것은 성공한 review이며
local fallback을 호출하지 않는다.
Packet이 canonical evidence/impact 요구를 판정하기에 부족하거나 첨부가 전달되지
않았으면 verdict를 추측하지 말고 `attachment_or_context_failure`로 fallback한다.

Local xhigh fallback은 review 결과 자체를 얻지 못한 경우에만 한 번 fresh/read-only로
허용한다. `fallback_reason`은 다음 중 정확히 하나다:
`provider_send_failure`, `model_or_effort_unconfirmed`, `timeout`,
`finality_failure`, `attachment_or_context_failure`. Pro verdict가 불리하거나 issue가
많다는 이유는 fallback이 아니다. fallback도 실패하면 gate는 `NEEDS_CONTEXT`로
닫는다.

Artifact에는 실제 실행 경로의 `reviewer_provider`, `reviewer_transport`,
`reviewer_model`, `reviewer_reasoning_effort`, `reviewer_session_id`,
`fallback_reason`을 기록한다. Pro 성공이면 provider/transport/model/effort는
`chatgpt_web`/`agbrowse`/`pro`/`extended`, session id는 non-null, fallback reason은
null이다. local scoped 또는 fallback이면 provider/transport는
`codex_local`/`subagent`, session id는 null이다.

Scoped reviewer가 실행 중 exact full-escalation predicate를 발견한 경우 그
`NEEDS_CONTEXT` 응답은 terminal attempt artifact가 아니라 routing envelope다. 같은
attempt/candidate/parent를 유지해 full route로 즉시 재dispatch하고, full 결과만
attempt artifact로 저장한다. 다른 `NEEDS_CONTEXT`는 terminal 결과로 저장한다.

모든 local profile은 `sandbox_mode = "read-only"`를 명시한다. attempt 1은 lineage의
baseline full review이고, BLOCKED/BROKEN fix 뒤 attempt M+1은 scoped가 기본이다.
full 재검증은 owner contract의 explicit escalation predicate가 있을 때만 위 full
primary/fallback route로 보낸다.
