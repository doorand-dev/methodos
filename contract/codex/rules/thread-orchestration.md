# Thread Orchestration

배포 경로: `~/.codex/rules/thread-orchestration.md`.

활성 프로젝트 오케 계약이 있으면 그 계약이 이 문서보다 우선한다.
`ORCA_TERMINAL_HANDLE`이 있는 legacy terminal에서는 오케 작업을 진행하지 않는다.

## 도구 매핑

- SPAWN(워커 생성) = native spawn thread/collaboration.spawn_agent(자기 자식 한정, agent_name 소문자_)
- SEND(세션 간 메시지) = Desktop thread 네이티브
- WAKE(턴 종료 후 재개 신호) = Desktop automations(`automation_update`)
- PROVE(완료 증거) = 커밋/파일. SEND/WAKE 성공·thread 상태는 완료 증거가 아니다.

## Thread vs subagent

- 구현 slice 라우팅(직접 실행/`luna-high-worker` 위임/조건부 리뷰)은 전역 `impl`
  스킬이 정본이다. 이 문서는 독립 thread 오케만 소유한다.
- 부모 턴 안에서 결과를 회수해 판단을 계속할 작업은 built-in subagent로 실행한다.
- 사용자 표시가 필요한 작업과 세션 경계를 넘는 위임은 독립 thread로 만든다.
  독립 thread 발주에는 전역 AGENTS.md의 회신 계약을
  포함한다. 중첩 위임을 허용하는 발주에는 "terminal 전에 네 자식 thread를
  아카이브하라"를 함께 넣는다.
- **ORCH-OWNER-001** — 독립 thread의 발주자(스포너)가 terminal 회수·판정과
  아카이브를 소유한다.

## Ordering과 병렬

- 시작 전 파일·의미적 계약·검증 전제의 overlap을 판정한다. 겹치면 직렬화하고,
  겹치지 않는 lane만 병렬 dispatch한다.
- dispatch는 lane당 정확히 한 번의 bounded 메시지로 보낸다. healthy busy thread를
  poll하거나 재촉 메시지를 보내지 않는다.
- 선행 thread가 끝나면 실제 diff가 후행 가정을 바꾸는지만 확인하고 재개한다.
- 기존 thread는 같은 goal·stage·ownership의 open lifecycle 안에서만 후속 지시를
  받는다. 같은 slice의 순차 substep·correction·reverification이면 재사용할 수
  있지만, 새 goal이나 새 slice는 fresh thread 또는 명시적으로 재선언한 worker로
  라우팅한다. terminal 이후에는 관련성만으로 재사용하지 않는다.

## 회수

독립 thread에 발주하면 턴을 끝낸다. 수행 thread가 parent thread로 terminal을
직접 보고하고, reply 도착이 발주자를 깨운다. 작업 길이는 판단 입력이 아니다.

`wait_threads` 대기는 단 한 경우만 허용한다: 사용자가 현재 턴에서 결과를
기다리고 있고 이번 응답에 그 결과가 필요할 때. 이때도 대기 1회 상한을 넘기면
반복하지 말고 턴 종료 + reply로 전환하고 사용자에게 그렇게 보고한다.

**ORCH-TERM-001** — terminal은 COMPLETED|BLOCKED|NEEDS_USER 하나와 증거(exact
changed paths, 실행한 검증 명령·결과, commit/HEAD)를 담는다. 메시지 수신·thread
상태·transport metadata는 완료 증거가 아니다.

## Heartbeat fallback

- one-shot heartbeat는 direct return 유실, crash, 의존 lane wake의 fallback이다.
  중간 보고 요구나 정기 polling 용도로 쓰지 않는다.
- 독립 thread에 발주한 발주자는 턴을 끝내기 전 one-shot heartbeat를
  arm한다. reply를 받으면 대기 중인 heartbeat를 삭제한다.
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
