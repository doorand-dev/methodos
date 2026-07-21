# Codex global context contract

배포 경로: `~/.codex/AGENTS.md`. 독립 Codex thread를 만들거나 다른 thread에
메시지를 보낼 때 아래 절을 전역 사용자 규칙에 포함한다.

Codex 배포에서는 `setup-methodos`, `using-methodos`, `conditional-heartbeat`를
설치하지 않는다. 구현 라우팅은 `impl`, 독립 thread와 heartbeat는 아래 전역 rules가
소유한다. `contract/codex/rules/`의 상대 구조를 `~/.codex/rules/`에 유지한다.

## 독립 세션 위임

create_thread·send_message_to_thread로 독립 세션에 일을 맡길 때는 발주 메시지에
회신 계약을 닫아 포함한다: 누가, 어디로(parent thread), 어떤 terminal 형식
(COMPLETED|BLOCKED|NEEDS_USER + 증거)으로 보고하고, 어떤 wake 경로로 회수되는지.
회수·ordering·heartbeat fallback 메커니즘은 활성 프로젝트 오케 계약이 정본이고,
없으면 `~/.codex/rules/thread-orchestration.md`를 point-of-use로 읽는다.
