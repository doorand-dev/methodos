# Codex global context contract

배포 경로: `~/.codex/AGENTS.md`. 독립 Codex thread를 만들거나 다른 thread에
메시지를 보낼 때 아래 절을 전역 사용자 규칙에 포함한다.

Codex 배포에서는 `setup-methodos`, `using-methodos`, `conditional-heartbeat`를
설치하지 않는다. 구현 라우팅은 `impl`, 독립 thread와 heartbeat는 아래 전역 rules가
소유한다. `contract/codex/rules/`의 상대 구조를 `~/.codex/rules/`에 유지한다.

## 역할 진입점

모든 task는 전역 AGENTS를 읽은 뒤 현재 explicit assignment와 nearest project
`AGENTS.md`의 crosswalk로 정확히 한 역할을 선택한다. 그다음 그 역할 계약과 프로젝트가
이름 붙인 constraints만 읽고 다른 역할 본문은 읽지 않는다.

- root controller → `~/.codex/rules/root-controller.md` + project adapter
- planning/multi-slice lifecycle lead → 활성 `plan` + `impl` + project constraints
- implementation worker → worker profile + exact packet + named project constraints
- fresh reviewer → reviewer profile + exact checkpoint packet
- standalone automation/observer → project prompt·adapter·durable state/output surface

역할 선택은 작업 시작 시점 한 번으로 끝나지 않는다. 같은 세션이 진단·감사·계획에서
구현·편집으로 넘어가는 등 역할이 실제로 바뀌면 그 전환점에서 crosswalk를 다시 적용해
새 역할과 그 계약을 읽는다. 작업이 작아 보인다는 이유로 이 재선택을 건너뛰지 않는다.

어떤 역할이든 승인된 baseline과 다른 user-visible behavior 가능성 또는 user-visible
visual/layout/output의 referent가 둘 이상의 구체적 대상으로 모호하게 남으면 active
`decision`의 `BEHAVIOR-AUTH-001`을 point-of-use로 적용한다. 명시적 기존 계약의 정확한
복원은 이 규칙만으로 formal plan을 요구하지 않는다.

사용자 발화가 의문문·서술인데 응답이 승인·발주로 이어지거나, 에이전트가 제시한 옵션을
사용자의 명시 선택 없이 확정하거나, 마지막 사용자 입력 이후 새 아키텍처·user-visible
결정을 내리면 진행 전에 그 판단의 출처를 사용자 발화와 대조해 명시한다. 사용자 발화에
문자 그대로 있으면 `[사용자원문]`, 발화에서 도출했으면 `[추론]`, 사용자가 언급한 적
없으면 `[내판단]`이다. `[추론]`·`[내판단]`이 사용자 확인 없이 아키텍처나 user-visible
behavior를 바꾸면 `NEEDS_USER`로 정지한다. 이 표기는 이 세 조건에서만 쓰고 통상 출력에
상시 부착하지 않는다.

프로젝트 crosswalk가 있으면 역할이 둘 이상에 매핑되거나 어디에도 매핑되지 않을 때
`NEEDS_USER`를 반환한다. 아직 crosswalk가 없는 legacy project는 explicit assignment로
한 역할을 선택하고 같은 turn에 신규·legacy 역할 본문을 섞지 않는다. Worker와 reviewer는
별도 subrole이고 reviewer는 persistent co-owner가 아니다. Parentless standalone run은
delegated child로 분류하지 않는다.

## 독립 세션 위임

모델·소유자 우선순위는 현재 사용자 지시 → project role/model contract → 활성 전역
`plan`/`impl`이다. 프로젝트 모델 계약이 없으면 planning·diagnosis·integration·
multi-slice lifecycle lead는 Sol/medium, one-slice executor와 worker는 `impl`을 따른다.
독립 thread 생성 시 선택한 model·thinking을 실제 인수에 명시한다. 현재 owner가 닫힌
packet을 직접 실행해도 session model은 바꾸지 않는다. True one-slice transition과
model 왕복 금지는 `impl`이 정본이다.

감독하는 built-in subagent의 결과가 다음 판단을 gate하면 live tool schema가 허용하는
최대 `timeout_ms`로 `wait_agent`를 한 번 호출한다. 실행 wrapper가 재개 가능한 cell이나
session을 반환하면 새 wait, status, transcript query를 발행하지 말고 같은 wait를 재개한다.
Terminal wake는 recovery일 뿐이며 completion에는 역할이 선언한 evidence가 여전히 필요하다.

Explicit parent가 있는 delegated thread 발주는 parent, lifecycle identity, packet,
terminal scope·대상, wake 경로를 닫고 `thread-orchestration.md`를 point-of-use로 따른다.
Parentless standalone automation은 parent나 SEND terminal을 지어내지 않고 프로젝트가
선언한 state/output surface로 끝난다.
