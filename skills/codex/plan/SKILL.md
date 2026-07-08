---
name: plan
description: |
  spec 받아 슬라이스 분해 + signature/schema inline + verification type enum + self-review 3-dim + M1 결정 리스트 + M2 scenario delta.
  **자동 발동 (self-trigger, 라우터 없음)**: spec(`docs/specs/slug.md`) approved 직후, "이 spec 구현해/이어가", 또는 다슬라이스 비-trivial 작업이 구현 전일 때. "plan"·"계획 짜"·"PRD 작성"·"기능 분해" 발화에서 직접 진입한다.
  **사용자 결정 공간 (FORCE)**: M1 결정 리스트, plan approval, plan-verify escalation, M2 scenario delta approval은 건너뛰지 않는다. 해소 뒤 plan-verify → impl → impl-verify → impl-novelist는 model-driven 자율주행.
  **spec-novelist preflight (FORCE)**: spec frontmatter가 `novelist.required: true`인데 `status != done`이면 plan 합성을 중단하고 spec-novelist fold를 먼저 요구한다.
  **right-sizing (OPEN)**: 슬라이스 두께·P0 스파이크 유무는 상황으로 모델 판단. 명시 호출은 선택사항: `/plan slug 또는 거친 골`.
---

# /plan — PRD 상세화 (standalone, 사용자 결정 공간)

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: spec approved 직후, 또는 다슬라이스 비-trivial 작업 *구현 전*
- 자연어: "plan", "계획 짜", "PRD 작성", "기능 분해"
- 명시: `/plan <slug 또는 거친 골 한 줄>`
- right-sizing(슬라이스 두께·P0 스파이크)은 **OPEN** — 상황으로 모델 판단 ( FORCE/OPEN)

## 산출 artifact (강제)

`<plan_root>/<slug>.md` — Markdown frontmatter + body. `plan_root`는 nearest `AGENTS.md`/프로젝트 관례가 정하며, 없을 때만 Codex 기본값 `.Codex/plans`를 쓴다. **plan-verify-reviewer + impl agent가 paste 받음** (sp "Never make subagent read plan file" — 본문 self-contained 필수).

### Frontmatter schema

```yaml
---
slug: <kebab-case>
created_at: YYYY-MM-DD
status: draft | approved
spec_ref: docs/specs/<slug>.md   # D19 — Phase 2 신설. D16 skip 시 null
source_spec:                       # D21 — spec 입력 추적
  path: docs/specs/<slug>.md
  approved_at: YYYY-MM-DDTHH:MM:SS+09:00
  sha: <git blob SHA — drift 감지용>
approved_plan_revision: <git SHA>  # D21 — 사용자 마지막 승인 SHA (M2 diff 기준점)
verify_cycle: 1                    # D36  — escalate→user-decision→plan rev = 1 cycle
verify_attempt: 0                  # D13 — cycle 내부 0~3 카운터
escalation_reason: null            # D13 — N=3 또는 같은 critical 2회 반복 시 한 줄 (매 cycle reset)
goal: <한 문장>
architecture: <2-3 문장>
tech_stack: [..]
slices:
  - id: 1
    title: <한 줄>
    files:
      create: [<exact path>,..]
      modify: [<exact path>,..]
      test: [<exact path>,..]
    verification:
      type: unit_test | command | fixture | artifact | custom
      command: <executable command>
      expected_exit_code: 0
      # type별 추가 필드 — § Verification type enum 참고
    estimated_minutes: <2-30>
    # M1 결정 리스트 (D17, Phase 2 신설 — 사용자 결정 필요 자리만)
    decision_needed: false           # 기본 false (단순 HOW는 AI 결정)
    user_facing_scenario: null       # decision_needed=true일 때 쉬운 용어 시나리오
    recommended: null                # AI 추천 — 쉬운 말 + 사용자 체감 결과
    options: []                      # [{label, consequence},..] 쉬운 라벨 + 쉬운 결과
    # hitl/hitl_message 필드 제거됨  — D30 4 기준 모두 plan M1 또는 impl-verify로 흡수
self_review:
  coverage_gaps: []
  placeholders_found: []
  type_inconsistencies: []
---
```

**필드 강제 룰 (Phase 2 추가)**:
- `spec_ref`: D19 — `docs/specs/<slug>.md` 존재해야 함 (D16 skip 케이스만 null 허용)
- `source_spec.sha`: spec frontmatter SHA — drift 감지 (spec 바뀌면 plan 재합성 필요)
- `approved_plan_revision`: 사용자가 명시 승인한 commit SHA. M2 diff 기준점
- `verify_attempt`: 0=초안, 1=plan-verify 1차 후 자동 수정, 2=2차 수정 (D13 한계)
- `decision_needed`: D17 판정 기준 — 사용자 체감 분기 / 비가역 / 사용자 자산 영향 중 하나 이상

### Body 구조 (sp `writing-plans` 차용)

```markdown
# <Feature> Implementation Plan

**Goal:** <한 문장>
**Architecture:** <2-3 문장>
**Tech Stack:** <key tech>

---

### Slice 1: <title>

**Files:**
- Create: `exact/path/file.py`
- Modify: `exact/path/existing.py:123-145`
- Test: `tests/exact/path/test.py`

**Decision-encoding inline** (signatures + schemas only — § Inline 정책):
```python
def update_profile(user_id: int, fields: ProfileUpdateRequest) -> User:
    """Validates and persists. Raises ValidationError on invalid input."""

class ProfileUpdateRequest(BaseModel):
    name: str = Field(.., min_length=1, max_length=100)
    email: EmailStr
    avatar_url: HttpUrl | None = None
```

**Steps** (TDD 5-step when verification.type=unit_test, else 자유 step):
- [ ] Step 1.1: Write failing test
- [ ] Step 1.2: Run test, verify FAIL
- [ ] Step 1.3: Implement minimal
- [ ] Step 1.4: Run test, verify PASS
- [ ] Step 1.5: Commit (WHY: prefix)
```

## 절차 (8 단계)

1. **spec 입력 수신** (D19): `docs/specs/<slug>.md` 읽기. spec status=approved 확인. 없으면(D16 skip 케이스) 거친 골에서 직접 합성.
   - nearest `AGENTS.md`/프로젝트 관례로 `plan_root`와 `verify_root`를 정한다. 프로젝트가 `.claude/plans/`를 정본으로 선언하면 그 경로를 쓰고, 없을 때만 `.Codex/plans`를 쓴다.
   - **novelist preflight**: spec frontmatter `novelist.required: true && novelist.status != done`이면 합성 중단. 사용자에게 보고하고 grill-me §6b(`spec-novelist` 1회 dispatch → fold → `status: done`) 선행. `novelist` 필드 부재(구버전 spec)는 경고만 하고 진행.
   - frontmatter `spec_ref: docs/specs/<slug>.md` 기재
   - spec의 user_stories/out_of_scope/edge_cases/modules를 *입력으로 받음* (추가 인터뷰 없이, to-prd 정신)
   - 충돌 결정 검색은 spec.md에서 이미 했음 — plan은 *받아 합성*만

2. **File Structure 설계** (sp 차용): task 정의 *전*에 file map 그리기.
   - Create / Modify / Test 라벨 명시
   - 책임 단위 분할 — files that change together live together
   - 기존 컨벤션 따름

3. **슬라이스 분해** ([3H] vertical, D23 thin 우선):
   - DB → 로직 → 화면 관통 줄기
   - 의존성 순서
   - 각 slice = 혼자 작동·검증 가능
   - *thin 우선* — 한 slice가 단독 검증 가능한 관찰 단위보다 크거나 독립 PASS artifact 하나로 설명 불가하면 split
   - **위험-우선 정렬 + P0 스파이크** (조건부 — [2J] Evidence + [3H]):
     슬라이스 순서 확정 *전*, *가장 불확실하고 틀리면 비싼* 가정 1개를 식별. **있을 때만**:
     - **P0 = throwaway 스파이크를 첫 단계로** — 프로덕션 코드 0, 그 가정 하나만 실측. `verification.type: artifact`로 *측정 결과를 `.plans/<slug>-spike.md` 또는 `docs/experiments.md`에 기록*(must_exist) = Evidence. 본문·title에 `P0 스파이크 (throwaway)` 명시.
     - 나머지 슬라이스는 *위험이 일찍 드러나게* 정렬 (순수 의존성 순서보다 위험 먼저) — 쉬운 기반부터 짓다가 늦게 가정 붕괴로 헛수고하는 패턴 차단.
     - **조건부 강조**: 가정이 다 알려진 routine 작업엔 P0 *없음* — 의식화(매번 빈 P0) 금지. 진짜 불확실+비싼 자리에만.
     - *impl-verify 처리 (자리만 — 상세 구현 시)*: spike 슬라이스는 프로덕션 기준(out_of_slice·signature 대조) 면제, 산출은 *기록된 측정값*만. 마커는 구현 단계서 확정.

4. **Decision-encoding code inline** (§ Inline 정책 참고):
   - function/method signatures (full)
   - type/dataclass/BaseModel schemas
   - test skeletons (assertions)
   - fixture shapes

5. **Verification type 선언** per slice (§ Verification type enum 참고).

6. **TDD step-by-step** (sp 5-step, verification.type=unit_test일 때):
   - Write failing test → Run+Verify FAIL → Min impl → Run+Verify PASS → Commit
   - 다른 type은 slice-level verification 1-2 step만

7. **M1 결정 리스트 생성** (D17,  신설):

   각 슬라이스 작성 중 *사용자 결정 필요* 자리는 slice frontmatter에 기재:

   ```yaml
   slices:
     - id: N..
       decision_needed: true
       user_facing_scenario: "<쉬운 용어 시나리오>"
       recommended: "<AI 추천 — 왜 이게 나은지 사용자 결과로 설명>"
       options:
         - {label: "<옵션1>", consequence: "<쉬운 결과>"}
         - {label: "<옵션2>", consequence: "<쉬운 결과>"}
   ```

   **사용자 표시 언어 규칙**:
   - 내부 용어를 질문 제목으로 쓰지 않는다: `verification.type`, `dispatch`, `schema`, `artifact`, `reviewer`, `M1/M2`, `slice` 같은 말은 숨기거나 괄호 뒤로 보낸다.
   - 질문은 "이렇게 하면 사용자가/운영자가 무엇을 보거나 해야 하는가?"로 쓴다.
   - 추천은 한 줄로 먼저 말한다. 선택지는 2-3개, 각 consequence는 장점·불편을 쉬운 말로 쓴다.
   - 기술적으로 중요한 위험은 "데이터가 덮일 수 있음", "나중에 다시 고치기 어려움", "작업이 중간에 멈출 수 있음"처럼 결과로 번역한다.

   **D17 판정 기준** — *하나 이상* 충족 시 `decision_needed: true`:
   - (a) 사용자 체감 시나리오 분기 (사용자가 보는 flow가 갈림)
   - (b) 비가역 (한번 정하면 바꾸기 비쌈)
   - (c) 사용자 자산·권한 영향 (데이터·돈·접근 권한 등)

   *단순 HOW* (라이브러리 선택, 내부 자료구조, 파일 구조)는 `decision_needed: false` — AI 결정.

   **plan 중간 HITL 게이트 신설 금지** : 사전 결정은 M1 `decision_needed`, 사후 검증은 `impl-verify` gate로 라우팅.

   **spec edge_cases 중복 회피 룰** (dry-run friction #3/#4):
   - spec.edge_cases에 `kind: decision` + `decision_status: user_confirmed` 자리는 *plan M1 skip* (사용자가 spec 단계에서 이미 명시 confirm)
   - spec.edge_cases에 `kind: decision` + `decision_status: ai_recommendation_only` 자리는 *plan M1에서 한 번 더 confirm* (spec에선 AI 추천만 있었음)
   - 사용자가 같은 결정 두 번 받지 않게 보장

   plan body 완성 후 → 사용자에게 결정 리스트 *한 번에* 표시:
   ```
   D1. [로그인] 기존 사용자가 비밀번호 잊으면?
       → 추천: 이메일 링크 재설정 (다른 옵션: SMS / 보안질문)
   D2. [데이터] 첨부 파일 크기 한도?
       → 추천: 25MB (다른 옵션: 10MB / 100MB)
   ```
   사용자 선택 → plan frontmatter `recommended` 또는 사용자 선택값으로 기재.

8. **Self-Review 3-dim** (sp 차용, by AUTHOR 30초):
   - **Coverage gaps**: spec user_stories 각 요구사항을 슬라이스에 매핑. 빠진 거 명시
   - **Placeholders found**: 본문 grep — "TBD" / "TODO" / "add appropriate" / "similar to slice N" 검출
   - **Type inconsistencies**: signature 이름·인자·반환 타입 슬라이스 간 일치 확인
   - **frontmatter `self_review:` 필드 기재** — 빈 array면 통과, 채워졌으면 fix 후 *다시 셀프 리뷰*. *빈 채로 status=approved 금지* ([2J] Evidence-grade)

9. **사용자 검토 1-3턴 + 명시 승인** — status: draft → approved. frontmatter `approved_plan_revision: <SHA>` 기록 (D21).

9b. **decision-reviewer 자동 호출** (D25/D26 + D33  — 런타임 tier 값 아니라 *게이트가 직접 관찰하는 상황 신호*로 발동):

    plan status=approved 직후 자동 호출 조건:
    - **아키텍처/보안 변경** (창발 L): 항상 자동 (D25)
    - **결정 자리 많음**: `decision_needed=true` slice가 ≥2 또는 *비가역/사용자 자산 영향* 결정 있으면 자동 (D33,  — F1 보강)
    - 그 외(소규모·결정 거의 없음): skip

    호출 결과 처리 (공통):
    - Codex에서는 프로젝트 worker thread가 아니라 `decision-reviewer` subagent role을 사용한다. 호출하지 않으면 plan/verify artifact에 reviewer downgrade 사유를 남긴다.
    - status=DONE → 다음 단계 (10. plan-verify)로 넘김
    - status=DONE_WITH_CONCERNS → plan SKILL conv로 issue 반영 → plan-verify로 넘김
    - status=BLOCKED → 사용자 escalate (D35 schema 적용)

    사용자 체감: 큰 결정 자리에 "나중에 바꾸기 어려운 선택이 있어 한 번 더 확인했어요"처럼 쉬운 말로 알림 (액션 0).

10. **/plan-verify 자동 트리거 + 자동 수정 conv + cycle 흐름** (D10/D13/D35/D36):

    plan-verify-reviewer agent 격리 검증 → BLOCKED 시 plan SKILL이 conv로 자동 수정:
    - Codex에서는 `plan-verify-reviewer` subagent role을 사용한다. 기존 작업 thread나 PONCOU worker thread를 reviewer로 재사용하지 않는다.

    - **N=3 한계** (D13) — cycle 내부 `verify_attempt` 카운터 frontmatter
    - **cycle 카운터** (D36,  F4) — escalate→user-decision→plan rev = 1 cycle. `approved_plan_revision` SHA 바뀌면 `verify_cycle += 1`, `verify_attempt = 0`, `escalation_reason = null` reset
    - 각 attempt 산출: `<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json` (D36 경로 갱신)
    - attempt 3 BLOCKED 또는 같은 critical 2회 반복 → escalate
    - **escalation 표시** (D35,  F3): plan-verify-reviewer가 `user_facing_escalation` 필드 생성 (M1 결정 리스트 schema 재사용 — `blocked_scenarios` + `decision_options`). plan SKILL은 *전달만*, 변환 X. 사용자 응답 → slice frontmatter `recommended` 1:1 매핑
    - **자동 재진행** (D36): 사용자 결정 → plan SKILL conv 수정 → plan-verify 자동 재호출 (사용자 명시 명령 X). 새 cycle 시작
    - **Cache 윈도우 5분 유지** : attempt N BLOCKED → 즉시 자동 수정. cycle 사이 사용자 결정 자리만 cache miss 감수 (의도된 trade-off)

    수정 도중 *옵션·임시방편 발화* 감지 시 → `decision` 스킬 자연어 자동 발동 (band-aid 방지).

    사용자 체감: escalate 시 기술 세부가 아니라 *막힌 상황·선택지·결과*를 쉬운 말로 표시 (라운드트립 X). 결정 후 *자동 재진행* — "(다시 확인 중..)" 알림만.

11. **M2 scenario delta approval** (D11, 조건부,  신설):

    **delta 서사 (inline)**: M2는 diff *제시*(presentation)에 더해, 변화를 **실사용자 시점의 쉬운 delta 서사**로 푼다 — "기존엔 …였는데, 이제 사용자가 …하면 …된다". inline 실행(기계적 SHA diff라 오염 여지 적어 외부 agent 불필요). 이때 *새 보완점*이 잡히면(서사화가 노출) → spec `edge_cases` / plan slice에 fold(presentation-only 아님).

    plan-verify 통과 후 *수정된 최종 plan* vs *사용자 승인 plan* diff 평가:

    - **변화 추출 대상** (사용자 체감만 노출):
      - spec.user_stories 매핑 변화 (어떤 story가 다른 slice로 이동)
      - spec.out_of_scope 변화 (범위 안/밖 변경)
      - spec.edge_cases 매핑 변화 — **D27 그레이존**:
        - 같은 slice 내부 분리 → 체감 X
        - *다른 slice로 이동 + verification.type 변경* → **체감 O** (사용자 표시)
        - 다른 slice로 이동 + verification 같음 → 체감 X (slice 경계 재조정)
      - slice의 user_facing_scenario 변화
      - decision_needed/recommended/options 변화
    - **숨기는 변화** (기술 잡음):
      - files.create/modify/test 변화
      - signature/schema inline 변화
      - verification.type 변화 (사용자 체감 무관, 단 D27 그레이존 예외)
      - slice split/merge (동일 user flow 유지 시)

    **분기**:
    - *체감 변화 없음* → 사용자에게 **한 줄 알림 + escape** (D34,  F2):
      ```
      plan-verify N차 후 자동 수정 완료. 체감 변화 없음 — model-driven 순차 구동.
      (자세히 보려면 'show' 발화)
      ```
      → 사용자 enter/대답 없음 → 다음 단계 (12) model-driven 순차 구동
      → 사용자 'show' 발화 → 변경 slice/필드 diff 전체 표시 → 사용자 결정:
         - 계속 → model-driven 순차 구동
         - 거부 → plan SKILL conv 재돌림 (새 cycle 시작, D36)
    - *체감 변화 있음* → 사용자 시나리오만 보고:
      ```
      변경 사항:
      - 기존: 회원가입 → 자동 로그인
      - 변경: 회원가입 → 이메일 인증 후 로그인 (reviewer 지적: 보안)
      ```
      사용자 승인 → frontmatter `approved_plan_revision: <new SHA>` 갱신 → cycle 카운터 갱신
      사용자 거부 → plan SKILL conv 재돌림 (새 cycle, D36)

12. **model-driven 순차 구동** (D20, 자율주행):

    plan status=approved 후 **모델이 plan-verify → 조건부 사용자 결정 공간(plan-verify escalation, M2 scenario delta approval) → impl(슬라이스별) → impl-verify gate(oracle/self-review/AST0/batch seam 가능) → impl-novelist(다파일 ∨ 다flow 최종 통합 서사)**를 순차 구동하고, 각 스테이지 경계에서 artifact 흔적(`<verify_root>/*.json` status·`WHY:` commit·`docs/adr/` 존재)을 직접 확인한다 (artifact 계약). 거대 조건문을 생성·복붙하지 않는다. 사용자 경험의 what 변경·비가역·사용자 자산 영향이 새로 생기면 그 결정만 묻고, 해소 후 자동 재진행한다.

## Inline 정책

agent가 plan 받으면 *interface symbol 모른 채* re-derive 부담 → signature·schema는 inline (paste-to-reviewer 같은 세션 모델이라 stale 우려 무).

### YES inline (decision-encoding)

- function/method signatures (인자 타입·반환 타입 포함)
- type/dataclass/BaseModel/interface schemas
- test skeletons (assertion 포함, 단 fixture data 짧게)
- fixture shapes (예시 dict/JSON 1개)

### NO inline (full algorithm/dump)

- 알고리즘 본체 — /impl 영역
- full file 복사 — 변경 자리만
- 기존 코드 그대로 paste — 변경 diff만

### Stale 위험 방어

- plan-verify-reviewer가 plan ↔ 기존 코드 drift 검출 (4 차원 D 정합성)
- `impl-verify` gate Stage 1이 plan signature ↔ 실제 commit signature 직접 대조

## No Placeholders (sp Red Flag 직접 port)

**Plan 실패** — 절대 작성하지 말 것:
- "TBD" / "TODO" / "implement later" / "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (실제 test code 없이)
- "Similar to Slice N" (반복 — engineer가 슬라이스 순서 안 따라 읽을 수 있음 → repeat)
- 코드 변경 step에 코드 블록 없음
- 정의되지 않은 type/function/method 참조

self-review placeholders_found에 잡히면 **반드시 fix 후 재self-review**.

## Verification type enum (verification.type)

각 slice 1 type 선언. `impl-verify` gate Stage 1이 type 보고 실행.

| type | command/필드 | expected | 사용 |
|---|---|---|---|
| `unit_test` | `command: pytest tests/../test_X.py -v` | `expected_exit_code: 0` | pure function, schema, parser |
| `command` | `command: <shell cmd>` | `expected_exit_code: 0` + (옵션) `expected_output_contains: ".."` | scripts, integration smoke |
| `fixture` | `command: diff <actual> <expected>` 또는 snapshot tool | `expected_exit_code: 0` | data shape, render output |
| `artifact` | `path: <file>` | `must_exist: true` + (옵션) `must_match: <regex 또는 checksum>` | files, config, migration |
| `visual` | (command 없거나 screenshot/preview) `observe: "<무엇을 육안 확인>"` | 명시 기준 충족 (자율주행 시 스크린샷+비전 — impl-verify G-C) | UI·렌더·대시보드 (테스트 오라클 부재) |
| `custom` | `command: <cmd>` + 자유 평가 룰 | `interpretation: "<통과 기준>"` | 표준 안 맞을 때 escape hatch |

> **impl-verify 오라클 타입(G-B)과 정렬** : 위 type ↔ impl-verify 오라클 택소노미 대응 — `unit_test`↔tdd-parity · `command`↔live-dry-run · `artifact`↔spike-measurement · `visual`↔visual(G-C) · `custom`↔adversarial-review 등. impl-verify가 슬라이스 오라클 타입을 판정할 때 이 `verification.type`을 1차 신호로 읽는다 (두 분류 체계 일치).

## Self-Review 3-dim 실행 가이드

### Coverage gaps

```
사용자 발화·spec 의 *각 요구사항* 적어보기.
→ 슬라이스에 매핑. 매핑 안 되는 거 = gap.
→ frontmatter coverage_gaps: ["<누락 요구사항 한 줄>"]
```

### Placeholders found

```powershell
# plan body grep
Select-String -Path <plan_root>/<slug>.md -Pattern 'TBD|TODO|appropriate|similar to|fill in'
# 잡힌 줄 → frontmatter placeholders_found: ["<grep 결과>"]
```

### Type inconsistencies

```
slice 간 cross-grep:
모든 signature 추출 → 함수명·인자 타입·반환 타입 일관성 확인
S2 update_profile ↔ S3 saveProfile mismatch → frontmatter type_inconsistencies: ["S2 update_profile vs S3 saveProfile"]
```

**룰**: self_review 3 필드 모두 명시. 빈 array면 *통과*, 채워졌으면 fix 후 재self-review까지 status=draft.

## 안 하는 것

- 사용자 추가 인터뷰 (이미 안 것 합성)
- 알고리즘 본체 inline (signature만, /impl이 본체 채움)
- 측정 불가 Goal ("좋은 UX", "사용자 만족" — 측정 가능 형식으로)
- slice 경계 부재 (files.create/modify/test 빈 채 진행)
- self_review 빈 채 status=approved ([2J] 위반)
- plan을 뒷단 자율주행 전, 사용자 결정 공간에서 작성 — /plan은 사용자 결정 공간이 정본

## 다음 단계 (자연 흐름)

```
status=approved
   ↓ model-driven 순차 구동 (모델이 스테이지 경계 artifact 흔적 직접 확인)
model-driven 자율주행 공간
   ↓ /plan-verify reviewer (이미 작성된 plan 격리 검증)
   ↓ /impl 슬라이스별 + impl-verify reviewer
   ↓ 모든 PASS sentinel
종료
```

## Reeval

- Inline 정책이 *진짜 stale 부담*되면 (drift evidence 2회+) → Inline 정책 재검토
- self_review 3-dim이 *ritualization* (모델이 lie) 발견 시 → frontmatter 형식 강화 (예: 각 필드에 evidence 명령 필수)
- /plan을 사용자 결정 공간에 둔 게 *사용자 부담* 너무 크면 →  Reeval (조건부 자율주행 공간 내부 모드 복귀)
- **P0 스파이크가 의식화**(불확실성 없는데 P0 남발) 또는 *반대로 한 번도 안 쓰임*(2026-08까지 0회) 발견 시 → 트리거 조건 강화 또는 제거. spike 슬라이스 마커가 실제 필요해지면 schema 필드 1급화 (현재는 prose 표시)
