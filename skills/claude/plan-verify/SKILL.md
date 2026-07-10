---
name: plan-verify
description: |
  Isolated adversarial verification of a plan (4 dimensions: conflicts with past ADRs · decision [0]~[3J] principles · user global rules · plan internal consistency).
  **Self-trigger (no router)**: right after plan status=approved, before impl (detect `approved_plan_revision` SHA change). "plan 검증", "이 계획 어떻게 보여?", "plan-verify".
  **Evidence (FORCE)**: every issue must *directly quote* command output or file:line — no abstract pass ("looks fine"), no evidence from unrun commands. Output `.claude/verify-reports/plan-slug-verify-attempt-N.json`. Explicit: `/plan-verify slug`.
---

# /plan-verify — plan 격리 적대적 검증 (얇은 stub)

> *얇은 stub*. Reeval: sycophancy 2회 등장 시.
> 글로벌 설치 시 격리 agent(`plan-verify-reviewer`)가 돌고, 로컬(agent 미설치)이면 스킬로서 *외부 자료 대조*로 격리를 보완한다.

> **약어 지도** — 이 문서는 cross-project 수신자가 raw URL로 가져간다. 그 문서만 읽어도 그 자리에서 이해되게:
> - `[2J]` = "통과" 단언 전 실제 명령 출력을 직접 인용한다(미실행 명령 evidence 금지) / `FORCE` = 강제 — 빈 evidence면 자동 BLOCKED
> - 항상 walk하는 원칙: `[1C]` = 임시방편 위에 또 임시방편 거부 / `[1D]` = 발산하는 값(숫자·경로·계약)만 단일정본 / `[2H]` = 작업 시간 5~10배 과대평가 차단 / `[3I]` = 콜러 인터페이스는 작게·동작은 풍부(가짜 추상화 거부)
> - `scoped re-verify` = 2·3차 재검증은 plan 전체 재독 말고 *걸린 issue + 수정된 부분*만 / `sycophancy` = 검증자가 plan 작성자 비위 맞춰 통과시키는 것(이 게이트가 막는 것) / `greenfield` = 기존 코드 재사용 없는 새 코드(차원 D 면제)
> - `preflight` = semantic reviewer 앞에 도는 `hooks/common/plan_preflight.py` 기계 검사(SHA·placeholder·ownership·line budget). FAIL은 planner가 고치며 reviewer attempt 안 소모, PASS는 evidence로 인용 / `DONE baseline amendment` = 이미 DONE인 plan의 behavior-preserving 내부 보정 — frontmatter `amendment.baseline_status: DONE`+`scope`로 baseline 전체 아닌 delta만 읽음(source SHA·체감동작·권한/데이터·비가역·public contract·cross-slice 변화면 full 승격)
> - `D13`(attempt 3회 한계)·`D25/D26`(decision-reviewer 먼저 1회)·`D36`(승인 SHA 바뀌면 새 cycle). 조건부 원칙 `[3H]`·`[1B]`·`[3J]`도 이 문서 안에서 필요한 만큼 직접 적용한다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: 최초 status=approved 직후 전체 검증. **DONE baseline amendment**면 frontmatter `amendment.baseline_status: DONE`와 `scope`로 delta만 읽는다. source spec SHA, user-visible behavior, authority/data, irreversible operation, public contract, cross-slice ownership 중 하나가 바뀌거나 scope 밖 파일/가정이 나오면 full로 승격한다. (트리거 신호: `approved_plan_revision` SHA 변경 감지 — D36, escalate 후 사용자 결정으로 plan 갱신되면 새 cycle 자동 시작)
- 자연어: "plan 검증", "이 계획 어떻게 보여?", "plan-verify"
- 명시: `/plan-verify <slug>`

## 호출 순서 (D26 — 런타임 tier 아니라 *상황 신호*)

decision-reviewer가 발동한 경우 (보안·권한·공개 계약·사용자 자산·비가역·cross-slice ownership ∨ 결정 자리 많음 — plan §9b):
```
plan approved → decision-reviewer (자동 1회, D25) → 본 plan-verify-reviewer attempt 1~3
```

그 외 (decision-reviewer skip):
```
plan approved → 본 plan-verify-reviewer attempt 1~3
```

`decision_needed=false` + M2 delta 없음 + public behavior/authority/data 변화 없는 behavior-preserving 구조 보정은 decision-reviewer skip. 자명한 1-2파일 수정: 둘 다 skip 권장.

## 사전 조건

- `Test-Path .claude/plans/<slug>.md` ✅
- plan frontmatter status=approved
- `py -3 <methodos_root>/hooks/common/plan_preflight.py .claude/plans/<slug>.md --repo <project_root>` PASS. FAIL은 reviewer dispatch 전 planner가 고치며 attempt를 소모하지 않는다. PASS는 첫 artifact evidence에 인용.

## 산출 artifact (강제)

`.claude/verify-reports/plan-<slug>-verify-attempt-<N>.json` (N=1, 2, 3) — 필수 필드:
- `kind`: "plan-verify"
- `attempt`: 1, 2, 또는 3 (D13 N=3 한계)
- `status`: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- `evidence`: 최소 1개 (검증 명령 + 출력 인용)
- `issues`: critical / important / minor + `repeated_from_attempt` (이전 attempt에서 본 issue면 N 명시)
- `escalation_required` / `escalation_reason`
- `self_review`: 4차원

**자동 수정 흐름** (N=3, 벤치마크 차용):
- attempt N BLOCKED → plan SKILL이 conv로 자동 수정 → attempt N+1
- attempt 3도 BLOCKED 또는 `repeated_from_attempt`로 동일 critical issue 재등장 → `escalation_required: true` + 사용자 escalate
- 사용자에겐 *기술 세부 X* — 남은 사용자 체감 시나리오/결정 필요 여부만

**scoped re-verify (attempt 2~3)**:
- attempt 1만 plan 전체 fresh 독립 재독. **attempt 2~3은 전체 재독 금지** — 이전 `attempt-N.json`의 `issues`(걸린 것) + plan 수정 delta(diff 또는 변경 슬라이스)만 읽고 "그 issue 해소됐나 + 수정이 새 모순 만들었나" 두 가지로 범위 한정.
- 영속 `attempt-N.json`이 "무엇을 걸었나"의 메모리 — *해소 판정*은 수정본 직접 확인(독립성 유지, JSON 주장 그대로 인용 금지).
- 모델: scoped라 이미 쌈 → opus 유지. 더 짜려면 attempt 2~3만 sonnet 강등 *가능*(옵션).

**DONE baseline amendment**:
- 기본은 baseline 전체가 아니라 `amendment.scope` slice, 해당 path/contract, 그리고 baseline과의 diff만 fresh reviewer에게 paste한다.
- preflight PASS 뒤 semantic reviewer는 1회만 호출한다. 그 reviewer가 찾은 기계 결함은 preflight로 고친 뒤 1회만 scoped re-review한다.
- 동일 critical이 다시 나오거나 사용자 선택이 새로 필요할 때만 full review 또는 사용자 escalate한다. 단순 internal HOW 보정은 full baseline 재독 사유가 아니다.

## 절차 (얇음)

1. **preflight + 범위 결정** + plan 본문 읽기: preflight PASS를 evidence로 기록. 최초 approved plan이면 전체를 읽고, DONE amendment면 `amendment.scope`+delta만 읽는다. full 승격 predicate(source SHA·체감동작·권한/데이터·비가역·public contract·cross-slice·scope 밖 가정) 충족 시에만 baseline 전체를 읽는다. reviewer는 Agent 도구 정상 반환으로 회수 — watcher/heartbeat polling 금지.
2. ***적대적 검증* (격리 부재를 외부 자료 대조로 보완)** — 다음 4 차원 모두 점검:
   - **A. 과거 결정 충돌**: `Select-String -Path docs/adr/ -Pattern '<유사 키워드>'`. 충돌 결정 발견 시 issues.critical.
   - **B. decision 원칙 정합성** (조건부): decision-reviewer 산출이 paste에 있으면(돌았음 — [0][1A][1B][3H][3J] 이미 함) 그 5개는 *재순회 말고 해소만 확인*, `[1C][1D][2H][3I]`만 직접 walk. 없으면(skip된 작은 plan) 전체 walk — [1C][1D][2H][3I]는 *항상*. (walk 시: [3H] 적용? [1B] 옵션 표? [3J] 섣부른 *재사용* 추출 위반? — 크기·응집 분해·명시 요청은 위반 아님)
   - **C. 사용자 글로벌 룰** (runtime global instructions): "위임 문서 = 글쓰기" 위반? — plan 본문이 그 자리에서 완결되나(원칙·용어를 "외부 문서로 넘기기"로 떠넘기지 않았나)·헐거운 조건문("적절히/필요하면")이나 미정의 코드(잠김) 없나·사용자 결정 자리를 체감 시나리오로 기술했나.
   - **D. plan 자체 정합성 + 재사용 계약 실재**: 슬라이스 의존성 순환? touched_files 겹침? estimated_minutes 합리적? **(조건부) plan이 *기존 코드를 재사용/가정*하는 자리("reuse X", "call Y", "기존 Z 그대로")마다 실코드 grep → 실재 + 시그니처/필드 일치 확인.** 불일치(가정한 함수·필드·계약 부재/상이) → critical/important — 허구 계약 위 슬라이스(impl-verify서 튕겨 헛구현). 재사용 없으면(greenfield) skip. 존재·시그니처만 — 코드 품질은 impl-verify 영역.
3. **Evidence 강제** ([2J]):
   - 각 issue마다 `where` (file:line) + `recommend` (수정 방향)
   - *주관 평가 금지* — 측정 가능 근거 인용
4. **자기 점검** (Self-review 4차원):
   - Completeness / Quality / Discipline / Testing
5. **JSON 저장**: `.claude/verify-reports/plan-<slug>-verify-attempt-<N>.json`. lazy 생성. plan frontmatter `verify_attempt` 카운터 동기화.
6. **status 결정**:
   - critical 0 + important 0 → DONE
   - critical 0 + important ≥ 1 → DONE_WITH_CONCERNS
   - critical ≥ 1 → BLOCKED
   - 정보 부족 → NEEDS_CONTEXT

## 적대성 정신

스킬로 도는 경우(로컬) *외부 자료 4 차원 대조*로 적대성 확보 + reviewer 정신 강제:

> **"Do not trust the report. Verify by reading [the plan], not by trusting [the planner's claims]."** plan 작성자의 "이 정도면 됐다" 주장은 evidence 아님 — 4 차원 대조가 evidence.

→ 위 4 차원 대조가 "메인 컨트롤러 자기 점검"으로 *놓칠* 자리를 잡는다.

## 안 하는 것 (Red Flags)

- 추상 통과 ("괜찮아 보임", "should be fine") — 모든 issue *원문 인용*
- evidence 빈 채 DONE 기재 ([2J] 위반)
- **미실행 명령을 evidence에 기재** — "Report only what was actually verified" 위반 — 이 스킬의 Evidence 규칙 위반
- plan 본문 *수정* (검증자는 read-only)
- "Should I proceed?" 중간 확인 — 자동 진행

## Reeval

- sycophancy 시나리오 2회 등장 (verify-report DONE인데 실제 결함 발견) → 격리 강화 검토 (옵션 1 runtime agent directory promote)
- 4 차원 외 *놓친 차원* 발견 → 본문 확장
- 차원 D 재사용 계약 reality-check가 *false positive*(plan이 별칭·paste로 표현해 grep 실패) 잦으면 → 표현 규약 강화 또는 조건 축소. greenfield 위주라 6개월 0회 발동이면 제거 검토 (누적 방지)

---

## 실행 전후 확인

- 4 차원 verdict 직전 → [2J] Evidence (격리 검증 + 명령 출력 직접 인용)
