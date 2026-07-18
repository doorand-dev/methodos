---
slug: codex-slice-owner-controller-review
created_at: 2026-07-18
status: superseded
goal: Keep implementation ownership and risk-based review boundaries small and observable.
user_stories:
  - {actor: "개발자", feature: "slice owner가 선언 경로를 구현", benefit: "변경 범위와 테스트를 빠르게 확인한다"}
  - {actor: "유지보수자", feature: "위험한 통합 seam만 선택적으로 검토", benefit: "실제 안전 신호에 집중한다"}
out_of_scope: ["일반 작업의 자동 final review", "SHA/lineage/session provenance", "report or terminal packet schemas"]
---

# Codex slice ownership and review

이 문서는 이전의 자동 reviewer/증적 topology를 대체한다. 구현 owner는
선언된 경로를 수정하고 테스트와 exact-path 검사를 실행한다. 일반 작업은
여기서 종료한다. 새 user/public flow, shared contract/permission/data,
external state/concurrency/migration, 또는 여러 slice seam 통합 위험이 있을
때만 controller가 semantic review를 한 번 선택한다.

Review 결과는 caller에게 짧은 `PASS`, `NEEDS_CONTEXT`, 또는 path/line issue로
돌려준다. 사용자 승인 경계와 실제 provider 완료 상태는 유지하지만, 모델,
effort, transport, session, SHA, artifact, terminal, WHY/report를 완료 조건으로
삼지 않는다.
