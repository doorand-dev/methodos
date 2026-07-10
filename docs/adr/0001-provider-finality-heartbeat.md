# ADR 0001: Provider finality와 heartbeat 역할 분리

| Field | Value |
|---|---|
| Status | accepted |
| Date | 2026-07-10 |

## Decision

| Option | 지금 비용 | 누적 비용 | 판정 |
|---|---:|---:|---|
| A. 30–60분 fallback만 | 낮음 | 완료된 Pro 답변을 오래 못 받음 | 기각 |
| B. 외부 watcher가 heartbeat 가속 | 낮음 | 공개 API 밖 TOML mutation·중복 wake 위험 | 기각 |
| C. foreground provider completion event | turn 점유 | 10분 wall-clock 대기로 동시 작업성 저하 | 지원 capability 필요 |
| D. provider finality 유지 + sessionId 재수집 | 낮음 | 자동 wakeup 없음 | 현재 채택 |

| 불변식 | 적용 |
|---|---|
| Identity | `sessionId` 하나로 collect, unresolved 상태에서 재-send 금지 |
| Finality | provider `complete` + `completedAt` + 최소 길이 + stable hash |
| Scheduler | public API가 exact one-shot을 지원할 때만 세션당 active heartbeat 하나; 그 전에는 schedule blocker를 보고 |
| Cleanup | final collect 뒤 heartbeat 삭제·tab close 선택 |

| Reeval | 조건 |
|---|---|
| B 재검토 | 외부 watcher가 `automation_update`로 기존 heartbeat를 update할 공개 capability 제공 |
| C 재검토 | provider terminal event가 owning Codex turn으로 직접 전달되는 capability 제공 |
