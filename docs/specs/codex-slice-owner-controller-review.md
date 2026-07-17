---
slug: codex-slice-owner-controller-review
created_at: 2026-07-17
status: approved
review:
  by: user
  at: 2026-07-17T00:00:00+09:00
  notes: 사용자 "Go"와 후속 scoped-review 재사용 지시로 승인했다.
goal: Codex 구현을 한 slice당 한 owner agent로 닫고 reviewer transport는 controller가 소유하며 repair 재검토는 같은 reviewer thread를 재사용한다.
user_stories:
  - {actor: "개발자", feature: "한 slice를 한 구현 owner에게 맡김", benefit: "구현 worker의 nested reviewer stall과 transport 모순을 제거"}
  - {actor: "개발자", feature: "controller가 fresh checkpoint/final reviewer를 호출", benefit: "검토 독립성은 유지하면서 실행 상태와 종료 경계를 한곳에서 관제"}
  - {actor: "개발자", feature: "repair를 같은 owner와 reviewer thread에서 scoped로 재검증", benefit: "전체 컨텍스트 재로딩과 중복 full review를 방지"}
out_of_scope: ["reviewer 자체 제거", "Claude impl topology 변경", "heartbeat·INFRA_ERROR 상태기계 구현", "LLM·UX discovery A/B gate 구현", "Luna/medium 기본값 도입"]
edge_cases:
  - kind: scenario
    flow: happy
    desc: "slice owner가 구현·검증·WHY commit을 반환하면 controller가 필요한 reviewer만 별도로 호출하고 다음 slice로 진행한다."
  - kind: scenario
    flow: edge
    desc: "reviewer가 BROKEN을 반환하면 controller가 stable finding을 같은 구현 owner에게 보내고, repair 뒤 같은 reviewer thread에 scoped packet만 보낸다."
  - kind: decision
    flow: edge
    desc: "다중 slice나 교차 모듈이라는 이유만으로 Luna/max를 사용할지"
    decision_status: user_confirmed
    recommended: "사용하지 않는다. 분해 후에도 남는 단일 slice의 고비용 불확실성 또는 Luna/high의 실증 실패가 있을 때만 max로 올린다."
    options: ["Luna/high 기본과 증거 기반 max 승격", "구조 규모만으로 max 승격"]
modules:
  create: []
  modify: ["impl·plan — 한 slice/한 owner 및 controller-owned reviewer routing", "impl-novelist·reviewer profiles — 같은 reviewer thread의 scoped follow-up", "using-methodos·setup-methodos·README·artifact contract — topology 동기화", "Codex active skills/agents — 정본과 동일하게 배포"]
testing_priority: ["plan preflight", "impl-novelist contract tests", "legacy nested reviewer 문구 부재", "정본과 활성 설치본 SHA-256 일치"]
---

# Codex Slice Owner and Controller Review Spec

## Problem

Codex 구현 worker가 slice 구현뿐 아니라 checkpoint/final reviewer spawn, repair,
artifact, terminal report까지 소유해 nested transport failure와 장시간 무응답이
구현 완료를 차단했다. 다중 slice·교차 모듈이라는 이유만으로 Luna/max를 선택해
개별 slice가 충분히 작아도 reasoning 비용과 stall 가능성이 커졌다.

## Solution

한 slice에는 한 구현 owner만 둔다. 구현 owner는 선언 경로의 구현, RED/GREEN,
로컬 검증, WHY commit과 구현 report에서 종료한다. Controller는 commit 경계를
확인한 뒤 위험 predicate에 맞는 checkpoint와 최종 조립 reviewer를 fresh하게 직접
호출하지만 semantic review를 직접 수행하지 않는다. BROKEN finding은 같은 구현
owner에게 repair packet으로 보내고, repair commit 뒤 attempt 1 reviewer의 같은
thread에 stable finding·repair diff·영향 selector만 scoped follow-up으로 전달한다.

Luna/high가 위임 구현의 기본이다. 다중 slice, 교차 모듈, 파일 수, plan 존재만으로
max를 선택하지 않는다. 분해 후에도 한 slice에 남는 원인·영향·검증 불확실성이
크고 오판 복구 비용이 높은 경우 또는 Luna/high가 실제로 수렴하지 못한 경우에만
max로 승격한다.

## Out of Scope

- Controller가 구현 파일을 수정하거나 semantic review를 대신하지 않는다.
- 일반 slice에 routine reviewer를 복구하지 않는다.
- 별도 repair-review profile을 유지하지 않는다.
- Claude 활성 하네스 파일은 변경하지 않는다.
