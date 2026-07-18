---
name: using-methodos
description: >-
  Methodos 분산 게이트 하네스의 패시브 오리엔테이션 — 게이트를 대신 라우팅하지 않고 프레임워크를
  설명만 한다. Fires: "methodos가 뭐야", "이 하네스 어떻게 동작", "어떤 게이트 있어", /using-methodos.
  Does not fire: "X 추가/구현/만들자" (← grill-me/plan 게이트가 직접 self-trigger. 이 스킬은 라우터가 아니다).
---

# using-methodos — 분산 게이트 하네스 오리엔테이션

이 파일은 **패시브 메타-doc**이다 — 프레임워크를 설명할 때만 읽는다. 작업을 *시작*하면 아래
게이트가 알아서 켜진다 (중앙 라우터 없음). "X 추가해줘"에 이 스킬을 부르면 그게 곧 라우터 부활이다.

## 라우터가 없다

각 게이트가 자기 상황 조건으로 자동발동한다 — quick fix는 무거운 게이트에 *안 걸리고*, 대형
기능은 grill-me부터 걸린다. 사용자는 tier·`/methodos` 같은 프레임워크 의례를 *체감하지 않는다.*
순서·강도는 트리거 조건에서 **창발**한다 (plan은 spec 있을 때, impl은 plan approved일 때).

## 게이트 지도 (각자 self-trigger, Claude 런타임)

| 게이트 | self-trigger 시점 | 산출 |
|---|---|---|
| `grill-me` | 새 capability·user-visible flow·미결정 WHAT, *코드 전* | `docs/specs/<slug>.md` (approved) |
| `plan` | spec 있거나 다슬라이스 비-trivial, *구현 전* | `.claude/plans/<slug>.md` (approved) |
| `impl` | plan approved 슬라이스·닫힌 execution packet | `WHY:` commit + 실행된 테스트 + changed-path 확인 |
| `decision` | 옵션 비교·비가역·임시방편 자리 | `docs/adr/NNNN-*.md` 또는 `WHY:` 주석 |
| `spec-novelist` | 여러 actor/flow의 spec | 누락 actor·flow (spec fold) |

**조건부 리뷰어** (fresh-context agent, 위험 predicate에서만 dispatch — prose 반환, JSON 아님):

| 리뷰어 agent | dispatch 시점 |
|---|---|
| `plan-verify-reviewer` | plan이 위험 predicate 건드림 |
| `impl-verify-reviewer` | 슬라이스가 위험 predicate 건드림 |
| `impl-novelist` | 다파일·다flow 골의 최종 통합 점검 1회 |

## 리뷰는 조건부다

기본은 로컬 테스트 + exact changed-path 확인으로 닫는다. **아래 위험일 때만** fresh-context
리뷰어를 dispatch한다: schema/public contract · authority/permission/security · persistence/
latest/idempotency/concurrency · migration/external state · order/financial execution ·
독립 슬라이스 여럿이 공유하는 foundation. 그 밖에는 로컬 검증으로 종결 — 매 슬라이스 자동 리뷰는 없다.

## 스킬 패밀리

| 갈래 | 스킬 | 역할 |
|---|---|---|
| Core gates | `grill-me`, `plan`, `impl`, `spec-novelist`, `impl-novelist` | spec → plan → 구현 → (조건부) 최종 서사를 직접 만든다 |
| Reviewers (조건부) | `plan-verify-reviewer`, `impl-verify-reviewer`, `impl-novelist` | 위험 predicate에서만 fresh-context dispatch, prose 반환 |
| Governance | `decision` | gate는 아니나 핵심 판단 렌즈 — 옵션 비교·비가역·임시방편·FORCE/OPEN을 닫는다 |
| Continuity | `handoff`, `snapshot`, `todo`, `context-novelist` | 긴 작업을 세션·압축·문서 경계 너머로 잃지 않게 한다 |

## 안전 경계 (의례 아님 — 유지)

테스트 실행 · exact changed-path 확인 · 외부작업/user data/permission/DB·schema/public
contract/concurrency/migration/external-state 승인은 유지한다. **실행에서 확인 못 하는
model·effort·transport·session 값, 생성 artifact 해시, commit 산문은 검증 완료나 gate 근거로
기록하지 않는다.** 완료의 근거는 실행된 테스트와 changed-path 확인이다.

## tier = 트리거 설계 근거 (런타임 라벨 아님)

tier(XS~L)는 런타임에 *존재하지 않는다* — 각 게이트의 트리거·right-sizing을 일관되게 짜기 위한
설계 근거로만 보존한다. 게이트는 상황(touched·결정 자리·flow)을 *조용히 자체 평가*해 무게를
정하지 "tier M입니다"라고 알리지 않는다.

이 문서는 역할을 설명할 뿐 실행을 대신하지 않는다. 구현·계획 문서의 point-of-use 조건이
충돌하면 그 문서를 따른다.
