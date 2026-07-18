---
slug: emergency-self-execution
created_at: 2026-07-18
status: superseded
goal: Close simple low-risk changes directly while preserving explicit risk and approval boundaries.
user_stories:
  - {actor: "개발자", feature: "작은 변경을 직접 실행", benefit: "불필요한 위임 지연을 피한다"}
out_of_scope: ["사용자 지정 실행 주체 변경", "승인 없는 외부 상태 변경", "모델/effort를 완료 증거로 취급"]
---

# Superseded execution guidance

Current routing lives in `skills/codex/impl/SKILL.md`. A simple closed change
may run directly when its files, tests, and failure boundary are clear. Ask
before changing user data, permissions, database/schema, public contracts,
concurrency/migrations, or external state. Otherwise use the active runtime's
normal implementation routing.

Completion is local tests plus exact changed paths. Risk review is conditional;
file count, model, effort, transport, session, hashes, or copied plan metadata
do not decide completion.
