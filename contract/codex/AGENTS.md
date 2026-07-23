# Codex global context contract

배포 경로: `~/.codex/AGENTS.md`. 독립 Codex thread를 만들거나 다른 thread에
메시지를 보낼 때 아래 절을 전역 사용자 규칙에 포함한다.

Codex 배포에서는 `setup-methodos`, `using-methodos`, `conditional-heartbeat`를
설치하지 않는다. 구현 라우팅은 `impl`, 독립 thread와 heartbeat는 아래 전역 rules가
소유한다. `contract/codex/rules/`의 상대 구조를 `~/.codex/rules/`에 유지한다.

## 독립 세션 위임

모델과 소유자 우선순위는 현재 사용자 지시 → 프로젝트 모델 계약 → 활성 전역
작업 계약이다. 프로젝트 계약이 없고 독립 task가 planning·diagnosis·integration
또는 여러 slice의 lifecycle을 소유하면 Sol/medium을 사용한다. 정확히 하나의
approved closed implementation slice를 실행하는 독립 owner와 구현 worker는
활성 전역 `impl` 계약을 따른다. 현재 owner가 닫힌 low-risk packet을 직접
실행할 때는 세션 모델을 바꾸지 않는다.

오케스트레이션 owner는 parent가 lifecycle terminal을 판정하기 전이고 open
HITL·child가 없으며 approved closed slice가 정확히 하나이고 planning thread의
context 재사용 가치가 높을 때에만, 그 독립 thread의 다음 turn에 명시적
`model`·`thinking`을 보내 구현 executor로 전환할 수 있다. 전환 발주는 exact
parent·slice·terminal 회신을 다시 선언한다. 전환한 thread는 그 slice만 소유하며
planning 또는 여러 slice lifecycle owner로 계속 확장하지 않는다.
구현 뒤 같은 lifecycle에서 Sol/medium lead로 다시 전환하지 않는다. 이후 planning,
checkpoint, repair ordering이 남으면 true one-slice가 아니므로 lead를 유지하고
built-in implementation worker를 사용한다. executor가 새 WHAT를 발견하면 스스로
planning으로 확장하지 않고 `BLOCKED|NEEDS_USER`로 parent에 반환한다.

create_thread·send_message_to_thread로 독립 세션에 일을 맡길 때는 발주 메시지에
회신 계약을 닫아 포함한다: 누가, 어디로(parent thread), 어떤 terminal 형식
(COMPLETED|BLOCKED|NEEDS_USER + 증거)으로 보고하고, 어떤 wake 경로로 회수되는지.
회수·ordering·heartbeat fallback 메커니즘은 활성 프로젝트 오케 계약이 정본이고,
없으면 `~/.codex/rules/thread-orchestration.md`를 point-of-use로 읽는다.
