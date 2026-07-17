---
slug: emergency-self-execution
created_at: 2026-07-16
status: approved
superseded_in_part_by: codex-slice-owner-controller-review
review:
  by: user
  at: 2026-07-16T00:00:00+09:00
  notes: 사용자 "ㄱㄱ"로 긴급 직접 실행 예외 권고안을 승인했다.
goal: 단순하고 닫힌 작업은 직접 실행하고, 위임이 필요한 일반 구현은 Luna/high를 기본으로 하되 고비용 실패 위험이 크면 Luna/max를 선택한다.
user_stories:
  - {actor: "개발자", feature: "명확하고 저위험인 작은 수정은 직접 완료", benefit: "불필요한 agent/thread 생성 없이 빠르게 검증·복구"}
  - {actor: "개발자", feature: "위임이 필요한 작업은 위험도에 맞는 Luna effort로 처리", benefit: "일반 작업의 품질과 실행 비용을 균형 있게 유지"}
out_of_scope: ["파일 수나 예상 시간만으로 직접 실행 허용", "고위험 checkpoint 또는 final review 우회", "사용자가 지정한 실행 주체의 독단적 변경", "실측 없는 Luna/medium 기본값", "모든 위임을 Luna/max로 고정"]
edge_cases:
  - kind: scenario
    flow: happy
    desc: "목표·변경 범위·회귀 검증이 명확하고 사용자 체감 flow·공개 계약·권한·데이터·비가역 변화가 없는 1~2파일 수정은 직접 실행한다."
  - kind: scenario
    flow: edge
    desc: "검증 실패·더 넓은 변경 필요·동시 수정·원인 불확정 중 하나가 생기면 직접 실행을 중단하고 Luna worker로 전환한다."
  - kind: decision
    flow: edge
    desc: "사용자가 Luna 실행을 명시한 경우 직접 복구 조건을 충족해도 실행 주체를 바꿀지"
    decision_status: user_confirmed
    recommended: "사용자 지정 Luna 실행을 유지한다. 직접 복구는 근거와 함께 제안만 한다."
    options: ["사용자 지정 실행 주체 유지", "에이전트가 직접 실행으로 독단 전환"]
modules:
  create: []
  modify: ["impl — 직접 실행 predicate와 Luna high/max 선택 기준의 단일 정본", "using-methodos·plan·setup-methodos — 기본 실행 경로와 impl 정본 참조", "SKILL-ARTIFACTS·checkpoint agent — worker effort 계약 동기화"]
testing_priority: ["정본과 활성 설치본의 file-set 및 SHA-256 일치", "직접 실행 및 Luna high/max 선택 기준의 중복 없는 참조"]
---

# Emergency Self-Execution Spec

> Codex의 기존 effort 승격 및 reviewer 호출 경계는
> `codex-slice-owner-controller-review`가 대체한다. 직접 실행 predicate는 유지한다.

## Problem

단순하고 닫힌 수정까지 강제 위임하면 agent/thread 생성 비용이 실제 위험보다 커진다. 반대로 위임 작업의 기본을 실측 없는 Luna/medium으로 낮추거나 모든 위임을 max로 고정해도 각각 재작업 위험과 추론 비용을 과대 부담한다.

## Solution

`impl`에 직접 실행 적격성 및 Luna high/max 선택 기준을 둔다. 직접 실행은 명확한 1~2파일 저위험 수정에 기본 적용한다. 위임이 필요한 일반 작업은 Luna/high를 기본으로 하고, 분해 뒤에도 한 slice에 남는 고비용·고복구비 원인·영향·검증 불확실성 또는 high의 실증 실패가 있을 때만 Luna/max로 올린다. Luna/medium은 비교 실측이 생기기 전 기본 경로로 사용하지 않는다. 나머지 스킬과 contract는 이 정본을 참조하거나 effort 범위를 정확히 반영한다.

## Out of Scope

- worker 기본 소유권을 직접 실행 기본값으로 바꾸지 않는다.
- 사용자 지정 Luna 실행을 자동으로 대체하지 않는다.
- 보안·권한·데이터·공개 계약·외부 상태 변경을 직접 실행 대상으로 넓히지 않는다.
