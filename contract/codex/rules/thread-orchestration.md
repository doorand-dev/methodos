# Thread Orchestration

배포 경로: `~/.codex/rules/thread-orchestration.md`.

활성 프로젝트 오케 계약이 있으면 그 계약이 이 문서보다 우선한다.
`ORCA_TERMINAL_HANDLE`이 있는 legacy terminal에서는 오케 작업을 진행하지 않는다.

## 도구 매핑

- SPAWN(워커 생성) = native spawn thread/collaboration.spawn_agent(자기 자식 한정, agent_name 소문자_)
- SEND(세션 간 메시지) = Desktop native `send_message_to_thread`. 오류 없이 반환한
  대상 `threadId`가 전달 증거다. 전달 의도·assistant 문구·thread 상태는 SEND가 아니다.
- WAKE(턴 종료 후 재개 신호) = Desktop automations(`automation_update`)
- PROVE(완료 증거) = 커밋/파일. SEND/WAKE 성공·thread 상태는 완료 증거가 아니다.

## Thread vs subagent

- 유효한 implementation owner가 된 뒤의 slice 라우팅(직접 실행/
  `luna-high-worker` 위임/조건부 리뷰)은 전역 `impl` 스킬이 정본이다. root
  controller가 implementation owner인지 판정하는 선행 gate는 이 문서가 소유한다.
- 부모 턴 안에서 결과를 회수해 판단을 계속할 작업은 built-in subagent로 실행한다.
- 사용자 표시가 필요한 작업과 세션 경계를 넘는 위임은 독립 thread로 만든다.
  독립 thread 발주에는 전역 AGENTS.md의 회신 계약을
  포함한다. 중첩 위임을 허용하는 발주에는 "terminal 전에 네 자식 thread를
  아카이브하라"를 함께 넣는다.
- **ORCH-OWNER-001** — 독립 thread의 발주자(스포너)가 terminal 회수·판정과
  아카이브를 소유한다.
- **ORCH-ROOT-001** — SPAWN 직전에 "나는 root controller인가, 대상은 product
  code인가?"를 판정한다. 둘 다 참이면 직접 구현하거나 implementation worker를
  SPAWN하지 않고 기존 관련 planning/multi-slice lifecycle owning task에 SEND한다.
  그 lead가 packet을 닫거나 갱신하고 true one-slice 전환 또는 자기 Luna worker를
  소유한다. 관련 lead가 completed/archived이면 먼저 unarchive하고 새 goal·stage·
  terminal을 명시한 bounded follow-up으로 새 lifecycle을 연다. duplicate lead를
  만들지 않는다. 관련 owner가 없으면 앱의 thread 생성 권한을 따르며, 사용자 권한이
  필요한 표면에서는 승인 없이 worker로 대체하지 말고 `NEEDS_USER`를 반환한다.
  routing을 위한 exact-path read-only 확인은 허용한다.
- root controller는 master integration mechanics와 runtime restart/config activation/
  HITL만 직접 소유한다. child terminal 뒤 product source repair는 WHAT이 그대로여도
  원래 lead에 돌려보낸다. 프로젝트 계약이 명시적으로 허용한 merge/conflict의
  기계적 해소는 승인된 behavior를 바꾸지 않을 때만 controller가 소유한다.
- root가 product worker를 잘못 SPAWN했고 이미 실행 중이면 취소하지 않는다. terminal
  뒤 exact result/commit을 관련 lead에 SEND해 acceptance와 integration ordering을
  맡기고 controller가 feature를 self-approve하지 않는다.
- pre-approval spec pass의 owner·trigger는 활성 `plan`/`spec-novelist`, planned
  implementation checkpoint의 owner·repair loop는 활성 `impl`이 정본이다.
  root controller라는 이유로 planning/multi-slice lead의 내부 gate를 대신하지 않는다.

## Ordering과 병렬

- 시작 전 파일·의미적 계약·검증 전제의 overlap을 판정한다. 겹치면 직렬화하고,
  겹치지 않는 lane만 병렬 dispatch한다.
- dispatch는 lane당 정확히 한 번의 bounded 메시지로 보낸다. healthy busy thread를
  poll하거나 재촉 메시지를 보내지 않는다.
- 선행 thread가 끝나면 실제 diff가 후행 가정을 바꾸는지만 확인하고 재개한다.
- 기존 worker thread는 같은 goal·stage·ownership의 open lifecycle 안에서만 후속
  지시를 받는다. 같은 slice의 순차 substep·correction·reverification이면 재사용할
  수 있지만, 새 goal이나 새 slice를 worker에 붙이지 않는다. planning/multi-slice
  lifecycle owning task가 계속 같은 domain owner라면 completed/archived 뒤에도
  `ORCH-ROOT-001`의 명시적 새 lifecycle로 재개할 수 있다. terminal은 worker callback이
  아니라 발주 parent가 review와 integration을 닫고 판정한 lifecycle terminal이다.
  관련성만으로 worker를 재사용하거나 lead를 조용히 계속 실행하지 않는다.

## 회수

독립 thread에 발주하면 턴을 끝낸다. 수행 thread가 parent thread로 terminal을
직접 보고하고, reply 도착이 발주자를 깨운다. 작업 길이는 판단 입력이 아니다.
`PLAN_READY|NEEDS_USER|COMPLETED|BLOCKED` report-up을 parent에 SEND한 child는 자기
turn을 끝내고 parent의 follow-up/wake로만 재개한다. child가 `wait_threads`나
`read_thread`로 parent를 회수·poll하지 않는다. parent 발주가 named decision에 대한
단 한 번의 synchronous wait를 명시한 경우만 그 bounded wait를 허용하며 반복하지
않는다.

**ORCH-RECOVER-001** — compact/resume 뒤 unresolved outbound는 SEND를 가정하거나
즉시 반복하지 않는다. 대상 `read_thread`의 최근 입력·turn id·status를 한 번 읽고
다음처럼 복구한다.

- `pending outbound`: 결정 뒤 matching follow-up 입력이 없고 대상의 이전 turn이
  terminal/idle이다. 한 번 SEND한다.
- `sent-but-unconfirmed`: SEND는 성공했지만 matching follow-up turn 시작은 아직
  보이지 않거나, 대상이 active/queued라 수신 여부가 불명확하다. 재전송하지 않고
  reply/wake로 회수한다.
- `confirmed-active`: matching follow-up 입력의 turn이 active/inProgress다. 재전송·
  polling하지 않는다.
- `terminal-consumed`: terminal을 읽은 뒤 parent가 review/integration/HITL 판정을
  자기 transcript에 남겼다. cursor 이동이나 메시지 열람만으로 판정하지 않는다.

동일 메시지 재전송을 막는 idempotency key는 현재 SEND에 없다. `read_thread`의
matching 입력이 중복 방지 근거이며, cursor/revision은 증분 조회 토큰일 뿐 SEND나
terminal 소비 증거가 아니다.

`wait_threads` 대기는 단 한 경우만 허용한다: 사용자가 현재 턴에서 결과를
기다리고 있고 이번 응답에 그 결과가 필요할 때. 이때도 대기 1회 상한을 넘기면
반복하지 말고 턴 종료 + reply로 전환하고 사용자에게 그렇게 보고한다.
SEND 확인, active 확인, compact/resume 복구에는 `wait_threads`를 쓰지 않는다.

**ORCH-TERM-001** — terminal은 COMPLETED|BLOCKED|NEEDS_USER 하나와 증거(exact
changed paths, 실행한 검증 명령·결과, commit/HEAD)를 담는다. 메시지 수신·thread
상태·transport metadata는 완료 증거가 아니다.

## Heartbeat fallback

- one-shot heartbeat는 direct return 유실, crash, 의존 lane wake의 fallback이다.
  중간 보고 요구나 정기 polling 용도로 쓰지 않는다.
- **ORCH-AUTO-001** — root controller를 target으로 하는 heartbeat는 root가 계속
  올바른 reader인 짧은 same-thread continuation이고 독립 product lifecycle이 없을
  때만 허용한다. next-window/multi-hour monitoring, diagnostics, provider/runtime
  observation, `PLAN_READY`나 repair로 확장될 수 있는 일은 root thread를 target으로
  하지 않고 같은 프로젝트의 standalone automation/new run으로 실행한다.
- standalone run의 prompt는 parent/controller, 기존 lifecycle owner, terminal 형식과
  evidence, report-up 대상을 명시한다. run은 자기 task/session context에서 workload를
  소유하고 terminal을 SEND한 뒤 끝난다. root는 automation 생성·갱신·삭제만 소유하고
  그 workload를 자기 turn에서 실행하지 않는다.
- 관련 lifecycle lead가 있으면 standalone run은 그 lead의 bounded observer/worker로
  evidence를 보고하며 acceptance·diagnosis·repair ownership을 새로 만들지 않는다.
  lead가 없을 때만 앱 권한에 따라 새 owning task로 만들고 root에 terminal을 보고한다.
  duplicate lead를 만들지 않는다.
- idle 독립 thread에는 외부 owner의 override follow-up 자체가 다음 turn을 시작한다.
  모델 전환만을 위한 별도 heartbeat는 추가하지 않는다.
- active thread가 자기 자신을 다음 turn의 다른 모델로 전환할 때는 예외적으로
  one-shot wake를 trigger로 쓸 수 있다. 먼저 exact transition marker를 담은 wake를
  arm하고, 같은 marker·`model`·`thinking`·pending task를 self-message로 보낸 뒤
  현재 turn을 끝낸다. wake는 자기 automation을 삭제한 다음 marker가 정확히 하나일
  때만 해당 task를 실행하고, 없거나 중복이면 `BLOCKED`로 끝낸다.
- 독립 thread에 발주한 non-root lifecycle owner는 필요할 때 턴을 끝내기 전 one-shot
  heartbeat를 arm하고 reply를 받으면 삭제한다. root controller는 독립 product
  lifecycle 때문에 자기 thread에 heartbeat를 arm하지 않고 `ORCH-AUTO-001`을 따른다.
- **ORCH-WAKE-001** — wake 턴은 자기 automation을 먼저 삭제하고, task transcript와
  Git 상태를 read-only로 다시 판정한다. unresolved 작업이 남을 때만 새 one-shot을
  하나 arm한다.
- 자식 thread의 마지막 메시지가 사용자 결정 대기이면 crash가 아니다. HITL 대기
  thread에는 재arm하지 않고 사용자 복귀를 기다린다.
- wake 판정이 crash이거나 BLOCKED에 대한 사용자 판정이 끝났으면, 발주자는
  재발주(새 thread) 또는 종결을 정하고 죽은 thread를 아카이브한다. terminal을
  이미 보고한 thread에 같은 작업을 재발주하지 않는다.

## Heartbeat 생성·삭제

- `automation_update` mode=create, kind=heartbeat, destination=thread를 쓴다.
- create에 DTSTART와 상대 `COUNT=1` 규칙을 넣지 않는다. one-shot RRULE은 정분
  grid 규칙만 쓴다. 60분 미만은
  `RRULE:FREQ=HOURLY;BYMINUTE=<mm>;BYSECOND=0;COUNT=1`,
  그 이상 24시간 미만은
  `RRULE:FREQ=DAILY;BYHOUR=<hh>;BYMINUTE=<mm>;BYSECOND=0;COUNT=1`.
- RRULE은 `~/.codex/rules/scripts/codex-heartbeat-rrule.ps1`로 생성하고 자연어
  시간에서 손으로 쓰지 않는다. 기존 automation 이동은 같은 스크립트의
  `-AutomationId ... -Apply`를 쓴다(TOML 직접 수정 경로).
- heartbeat prompt에 automation id를 넣고, wake 첫 단계는 같은 id의 automation
  삭제다. 성공 판정은 실제 wake 턴과 삭제된 automation으로 하고 UI 표시 문구로
  하지 않는다.
- 중복 생성 대신 기존 관련 heartbeat를 갱신한다.

## Thread 정리와 아카이브

- `ORCH-OWNER-001`의 발주자는 자기가 만든 자식만 아카이브하고, 남의 자식은
  아카이브하지 않는다.
- 중첩 위임(자식이 손자를 만든 경우)에서는 자식이 자기 terminal을 보고하기 전에
  자기 손자들을 먼저 아카이브한다. 자식의 terminal에는 미정리 자식이 남아 있지
  않아야 하며, 남으면 그 목록을 terminal에 포함한다.
- 아카이브 조건(모두 충족 시 즉시 아카이브):
  - terminal을 회수해 판정을 끝냈다.
  - 그 thread에 남은 HITL·사용자 결정이 없다.
  - 그 thread가 소유한 worktree의 통합 판정(integrated/보존/폐기)이 끝났고,
    worktree 후속 처리는 cleanup 대기열에 넘겼다.
- thread 아카이브와 worktree 정리는 별개다. 아카이브는 worktree를 삭제하지
  않으며, worktree는 `~/.codex/rules/worktree.md`의 대기열 절차만 따른다.
- 사용자 표시 thread와 HITL 대기 thread는 사용자 결정 없이 아카이브하지 않는다.
- BLOCKED terminal thread는 blocker 보고와 사용자 판정 전까지 아카이브하지
  않는다.
