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
Codex는 plan 승인 뒤 별도 `plan-verify`를 자동 호출하지 않고, 일반 slice commit마다
`impl-verify`를 만들지 않는다. 모든 slice는 로컬 RED/GREEN·선언 검증·diff 범위를
닫는다. 명시적 high-risk predicate에 맞는 slice만 fresh checkpoint를 한 번 거친 뒤
완성 후보에서 fresh final reviewer를 한 번 호출한다. 고위험 결정과 복합 spec 서사는
아래 조건부 reviewer만 앞단에서 실행한다.

| Gate | Scope | Primary | Model | Effort |
|---|---|---|---|---|
| spec-novelist (다중 actor/flow만) | one-shot | fresh local `spec-novelist` subagent | parent session 상속 | parent session 상속 |
| decision-reviewer (고위험 결정만) | one-shot | fresh local `decision-reviewer` subagent | parent session 상속 | parent session 상속 |
| impl checkpoint (선택된 high-risk slice만) | attempt 1 full once; repair scoped | fresh local `impl-checkpoint-reviewer` subagent | `gpt-5.6-sol` | `medium` |
| final impl-novelist | attempt 1 full | fresh local `impl-novelist` subagent | `gpt-5.6-sol` | `medium` |
| final impl-novelist | repair attempt 2+ scoped | fresh local `impl-novelist-scoped-reviewer` subagent | parent session 상속 | parent session 상속 |

Checkpoint predicate는 schema/public contract, authority/security, persistent
artifact/latest/idempotency/concurrency, migration/external state, financial execution,
또는 2개 이상 후속 slice 기반이다. 크기·복잡도만으로 발동하지 않는다. Attempt 1
full은 대상 slice당 정확히 한 번이고 routine second full은 없다. Repair 뒤에는 stable
issue/path/selector만 scoped로 재검증한다. 사용자가 `검토 1회만`이라고 제한한 작업은
scoped도 생략하고 residual risk를 final packet에 넘긴다.

Final full review는 approved requirements, candidate refs, 필요한 파일, 영향 graph,
검증 명령을 self-contained context packet으로 보낸다. Final full과 checkpoint
custom-agent TOML은 `gpt-5.6-sol`과 `medium`을 선언해 구현 부모 세션의 설정과
무관한 품질 하한을 둔다. spec·decision·final scoped profile은 `model`과
`model_reasoning_effort`를 생략해
부모 세션에서 상속한다. Packet이 canonical evidence/impact 요구를 판정하기에
부족하거나 reviewer를 실행할 수 없으면 verdict를 추측하거나 외부 provider로
fallback하지 말고 `NEEDS_CONTEXT`로 닫는다. 상속 동작의 upstream 근거는 Codex 공식
[Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)다.

사용자가 외부 Pro/Claude 검토를 명시적으로 요청하면 해당 provider skill/runtime의
session·model·finality 계약을 point-of-use로 읽고 별도 fresh review로 실행한다. 이
명시적 외부 검토 실패도 다른 외부 provider의 자동 호출 사유가 아니다.

Artifact에는 실제 실행 경로의 `reviewer_provider`, `reviewer_transport`,
`reviewer_model`, `reviewer_reasoning_effort`, `reviewer_session_id`,
`fallback_reason`을 기록한다. `fallback_reason`은 shared schema 호환을 위해
유지하지만 자동 fallback이 없는 Codex route에서는 null이다. 기본 local route의 provider/transport는
`codex_local`/`subagent`, session id와 fallback reason은 null이다. local full은
`gpt-5.6-sol`/`medium`을 기록한다. 부모 값을 상속하는 local profile은 runtime이 실제
값을 노출하면 그 값을 기록하고, 노출하지 않으면 각각 `inherited_from_parent`를
기록한다. 이 값은 unknown이 아니라 custom-agent 설정을 생략해 부모 세션에서
상속했다는 명시적 provenance다. 명시적으로 요청한 외부 검토는 실제
provider/transport/model/effort/session을 기록한다.

Final attempt 1은 요구사항/범위, caller·producer·consumer·실패경로, 품질/부채,
test oracle·regression의 4개 technical lens와 actor/user-story narrative overlay를
한 pass로 수행한다. 별도 final full `impl-verify`를 앞뒤로 붙이지 않는다. Gating
finding은 exact approved acceptance criterion, user story, explicit public invariant
backlink가 필수이고, reviewer는 특정 구현 대신 관찰 invariant와 최소 oracle만 요구한다.

Final attempt 1 DONE이면 종료하며 routine second review를 만들지 않는다. BROKEN fix로
새 candidate가 생긴 경우에만 attempt 2+ scoped reviewer가 stable issue closure,
repair paths, 영향받은 caller/producer/consumer/flow/test selector를 확인한다.
요구사항, acceptance/oracle, public contract, authority/data behavior, impact graph가
바뀌면 scoped를 full로 넓히지 않는다. 사용자 결정이 필요하면 먼저 닫고 새 lineage의
attempt 1 full로 시작한다.

모든 local profile은 `sandbox_mode = "read-only"`를 명시한다. Codex final artifact는
requirements/scope, impact/quality, fresh commands/full regression, actor/user-story
narrative를 함께 소유한다. `plan-verify`와 routine per-slice `impl-verify` artifact는
Codex lifecycle의 완료 조건이 아니다. 선택된 high-risk checkpoint artifact만 예외다.
