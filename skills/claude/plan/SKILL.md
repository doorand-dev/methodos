---
name: plan
description: >-
  승인된 spec(또는 거친 골)을 slice-by-slice 구현 계획으로 합성. 슬라이스마다 touched files,
  signature/schema(inline), 검증법, 사용자 결정 슬롯(M1)을 못박는다. Standalone — spec을
  입력으로 추가 인터뷰 없이 합성. 산출 .claude/plans/<slug>.md.
  Self-trigger: spec approved 직후 또는 다슬라이스 비-trivial 작업 구현 전 — "plan", "계획 짜", "기능 분해".
---

# /plan — 구현 계획 합성 (standalone, 사용자 결정 공간)

승인된 spec(`docs/specs/<slug>.md`) 또는 거친 골을 입력으로, **추가 인터뷰 없이** 슬라이스
단위 구현 계획을 합성한다. 산출은 `.claude/plans/<slug>.md` 하나 — impl과 (조건부)
plan-verify-reviewer가 *본문을 paste 받으므로* self-contained여야 한다(서브에이전트는 파일을
안 읽고 프롬프트에 적힌 것만 안다). spec↔plan 연결은 **공유 slug**가 준다 — 별도 포인터를 두지 않는다.

## 트리거 (self-trigger, 라우터 없음)

- spec approved 직후, 또는 다슬라이스 비-trivial 작업 구현 직전.
- "plan", "계획 짜", "PRD 작성", "기능 분해".
- 작은 수정(touched 1-2 · flow無 · 새 schema無)은 발동 안 함 → 바로 impl.

## plan이 담는 것

mechanical frontmatter(slug · `status: draft|approved` · slices의 files/verification/
`line_budget`/`public_contracts`+`public_callers`)와 preflight 안전 규칙의 **정본은 공유
contract**(`contract/SKILL-ARTIFACTS.md`)다 — 여기선 Claude 합성이 추가로 지는 것만 못박는다:

- **M1 결정 슬롯**: 사용자 체감 분기 / 비가역 / 사용자 자산 영향 중 하나라도면 그 슬라이스에
  `decision_needed: true` + `user_facing_scenario`(쉬운 용어) + `recommended` + `options`
  [{label, consequence}]. spec의 `kind: decision` edge_case가 `user_confirmed`면 skip,
  `ai_recommendation_only`면 여기서 한 번 더 confirm. plan은 *전달만* — 결정을 추정하지 않는다.
- **self_review** (3차원): `coverage_gaps` / `placeholders_found` / `type_inconsistencies`.
  채우고 gap 있으면 fix 후 *재self-review*까지 `status=draft`. **빈 채 approved 금지** ([2J] Evidence-grade).
- **body**: `# <Feature> Plan` → Goal / Architecture(2-3문장) / Tech Stack → 슬라이스별
  Files / Decision-encoding(signature·schema·test-skeleton inline, algorithm body는 X) / Steps.

JSON 보고서·SHA lineage·provenance·`drive_config`·`approved_plan_revision`는 **만들지 않는다.**
완료의 근거는 사용자 명시 승인과 preflight 통과다.

## right-sizing (OPEN)

슬라이스 두께와 P0 spike 필요 여부는 rigid 규칙이 아니라 상황 판단이다. 너무 두꺼우면
`line_budget`(1~200) 초과로 preflight가 막는다 — 그때 나눈다. spike는 실패 시 되돌리기 비싼
구체적 불확실성에만 — 일상 작업엔 불필요.

## 조건부 plan-verify 라우팅

기본은 verify 없음 — preflight(기계 검사) + 사용자 승인으로 종결한다. **plan이 아래 위험을
건드릴 때만** `plan-verify-reviewer` 에이전트를 fresh context로 한 번 dispatch한다:

- public flow/contract 변경 · authority/data 동작 · 비가역 연산 · external
  state/concurrency/migration · 독립 슬라이스 여럿을 가로지름.

리뷰어는 plan 본문 + 결정 맥락을 받아 scope · caller/producer/consumer 영향 · 슬라이스 경계 ·
명시 테스트를 점검하고 `PASS`/`NEEDS_CONTEXT`/이슈 bullet(path:line + 빠진 결정)을 반환한다.
JSON·해시·provenance를 요구하지 않는다. **advisory 1회** — plan을 자동 재작성하거나 verify
루프를 돌지 않는다. 발견은 사용자에게 전달, 결정은 사용자.

## 절차

1. spec 입력 수신(`docs/specs/<slug>.md`, status=approved 확인). 없으면 거친 골에서 직접 합성.
2. 슬라이스 분해 + Decision-encoding inline + M1 슬롯 채움.
3. self_review 3차원 → gap fix → 사용자 승인 요청.
4. 승인되면 `status=approved`. 위험 predicate면 plan-verify-reviewer 조건부 dispatch → 이후 impl.
