# Delegated Thread Transport

배포 경로: `~/.codex/rules/thread-orchestration.md`.

이 계약은 explicit parent가 있는 delegated task의 dispatch·report-up·recovery에만
적용한다. Parentless standalone automation은 이 계약을 읽거나 가짜 parent를 만들지
않고 프로젝트가 선언한 durable state/output surface를 따른다. 프로젝트 adapter는
role mapping과 archive/release eligibility를 소유한다.

## 도구 매핑

- SPAWN = native thread/subagent spawn. Built-in subagent는 호출 parent의 현재 turn 안에서
  결과를 회수할 때, 독립 thread는 사용자 표시나 session boundary가 필요할 때 쓴다.
- SEND = Desktop `send_message_to_thread`. 오류 없이 반환한 대상 `threadId`가 전달
  증거다. 전달 의도·assistant 문구·thread status는 SEND가 아니다.
- WAKE = Desktop automation/event wake. WAKE 성공은 workload 완료 증거가 아니다.
- PROVE = 실제 파일·commit·command result·required artifact/HITL이다.

## Dispatch identity

**ORCH-OWNER-001** — explicit parent가 packet terminal의 단일 소비자이고 자기가 만든
descendant의 transport 정리를 소유한다.

발주 prompt는 explicit parent, lifecycle identity, packet/slice, attempt, terminal
scope·대상, wake 경로를 명시한다. Worker와 reviewer는 별도 subrole이다. Worker는 closed packet만
구현하고 reviewer는 fresh/read-only이며 acceptance나 repair ownership을 갖지 않는다.

같은 worker/thread는 같은 open lifecycle·packet의 completion, correction,
reverification에만 재사용한다. 새 goal·scope·risk는 새 packet이다. Terminal lifecycle
뒤 같은 lead task를 재사용할 수는 있지만 새 lifecycle identity를 명시해야 하며 과거
lifecycle을 다시 열지 않는다.

## Report-up과 terminal scope

**ORCH-TERM-001** — terminal은 scope와 evidence를 포함하며 status나 transport
metadata만으로 완료를 주장하지 않는다.

- Worker `COMPLETED|BLOCKED|NEEDS_USER`는 assigned packet만 닫는다.
- Reviewer return은 finding/pass만 반환하며 packet이나 lifecycle을 닫지 않는다.
- Lifecycle lead terminal은 worker result, 조건부 review, repair/re-review를 소비한 뒤
  lifecycle을 닫는다.
- Root terminal은 프로젝트 integration·HITL 이후 overall request를 닫는다.

`PLAN_READY`는 lifecycle terminal이 아니라 approval을 위한 coordination output이다.
Lead는 SEND 뒤 turn을 끝내고 parent follow-up으로 같은 lifecycle을 재개한다.

Built-in subagent는 terminal을 caller에 direct return하고 caller가 소비한다. 독립 child는
terminal과 evidence를 parent에 SEND한 뒤 자기 turn을 끝낸다. Parent의 follow-up/wake로만
재개하며 `wait_threads`나 `read_thread`로 parent를 poll하지 않는다. Incomplete packet이나
새 WHAT는 role을 확장하지 않고 explicit parent에 `BLOCKED|NEEDS_USER`로 반환한다.

## Compact/resume recovery

**ORCH-RECOVER-001** — compact/resume 뒤 unresolved outbound는 SEND를 가정하거나
즉시 반복하지 않는다. 대상 `read_thread`의 최근 matching input·turn id·status를 한 번
읽고 복구한다.

- `pending outbound`: matching follow-up 입력이 없고 이전 turn이 terminal/idle이다.
  한 번 SEND한다.
- `sent-but-unconfirmed`: SEND는 성공했지만 matching turn 시작이 보이지 않거나 대상이
  active/queued다. 재전송하지 않고 reply/wake로 회수한다.
- `confirmed-active`: matching follow-up turn이 active/inProgress다. 재전송·polling하지
  않는다.
- `terminal-consumed`: parent가 matching lifecycle·packet·attempt terminal을 읽고
  판정을 transcript에 남겼다. 같은 terminal을 다시 소비하지 않는다.

현재 SEND에는 idempotency key가 없다. Matching input/terminal transcript가 중복 방지
근거이고 cursor/revision은 증분 조회 토큰일 뿐 SEND나 소비 증거가 아니다. Compaction은
lifecycle identity, packet, attempt, parentage를 바꾸지 않는다.

`wait_threads`는 사용자가 현재 turn에서 결과를 기다리고 이번 응답에 필요할 때만 한
번 bounded call로 사용한다. Timeout 뒤 반복 polling하지 않고 reply/wake로 전환한다.
SEND 확인, active 확인, compact recovery에는 쓰지 않는다.

## Wake mechanism

One-shot heartbeat는 explicit-parent direct return 유실, crash, dependency wake의
fallback이지 중간 보고·정기 polling workload가 아니다. Root의 deferred automation
소유권은 `root-controller.md`가 정본이다.

Active thread가 자기 다음 turn의 model transition을 위해 self-wake할 때는 exact marker를
arm하고 같은 marker·model·thinking·packet을 self-message한 뒤 현재 turn을 끝낸다.
Wake는 자기 automation을 먼저 삭제하고 marker가 정확히 하나일 때만 실행한다.

**ORCH-WAKE-001** — Wake turn은 automation을 먼저 삭제하고 task transcript와
프로젝트가 허용한 state를 read-only로 판정한다. User decision/HITL 대기를 crash로
취급하거나 terminal task에 같은 packet을 재발주하지 않는다. RRULE 생성은
`~/.codex/rules/scripts/codex-heartbeat-rrule.ps1`을 사용하며 automation 파일을 직접
편집하지 않는다.

## Archive mechanism

독립 thread spawner는 자기가 만든 descendant만 native archive할 수 있다. Archive eligibility,
retention, automation-origin 제외, worktree integration/release 조건은 프로젝트/role
계약이 소유한다. Thread archive는 worktree 삭제가 아니며 idle status만으로 둘 중
어느 것도 실행하지 않는다.

## Compatibility

Root-only `ORCH-ROOT-001`·`ORCH-AUTO-001`은 `root-controller.md`로 이동했다. 이 문장은
legacy project pointer를 위한 비규범 compatibility 안내이며 root contract를 복제하지
않는다.
