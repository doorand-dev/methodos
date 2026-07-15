---
name: plan-verify
description: |
  Isolated evidence-backed adversarial verification of an approved plan against past decisions, Methodos principles, user rules, and internal consistency. Self-trigger once per new approved revision; BLOCKED fixes receive scoped reverify. Do not fire without a formal plan, or for an explicitly requested single-slice plan touching 1-2 files with `decision_needed=false` and no user-visible behavior, authority/data, public-contract, or irreversible change; continue automatically. Explicit “plan 검증”, “이 계획 어떻게 보여?”, `/plan-verify` overrides the skip. Quote actual command output or file:line for every issue and explain escalations in plain Korean.
---

# /plan-verify — plan 격리 적대적 검증 (얇은 stub)

> *얇은 stub*. Reeval: sycophancy 2회 등장 시 ( 참고).
> Codex full review는 현재 부모 세션의 model/effort를 상속한 fresh local read-only
> subagent가 기본이다. 외부 Pro/Claude reviewer는 사용자 명시 요청 때만 쓴다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: 아래 작은 plan 자동 생략 조건에 해당하지 않는 최초
  status=approved 직후와 새 `approved_plan_revision` 직후. 승인된 amendment도 새
  lineage attempt 1 full로 시작한다. 같은 lineage의 BLOCKED fix만 attempt M+1
  scoped로 간다.
- 자연어: "plan 검증", "이 계획 어떻게 보여?", "plan-verify"
- 명시: `/plan-verify <slug>`

## 호출 순서 (D26  — 런타임 tier 아니라 *상황 신호*)

decision-reviewer가 발동한 경우 (보안·권한·공개 계약·사용자 자산·비가역·cross-slice ownership ∨ 결정 자리 많음 — plan §9b):
```
plan approved → decision-reviewer (자동 1회, D25) → 본 plan-verify-reviewer attempt 1~3
```

그 외 (decision-reviewer skip):
```
plan approved → 본 plan-verify-reviewer attempt 1~3
```

`decision_needed=false` + M2 delta 없음 + public behavior/authority/data 변화 없는 behavior-preserving 구조 보정은 decision-reviewer skip.

정식 plan이 없으면 이 게이트는 발동하지 않는다. 사용자가 작은 작업에도 plan을
명시 요청한 경우, plan이 단일 slice·touched_files 1-2개·`decision_needed=false`이고
사용자 체감 동작·보안/권한·데이터/사용자 자산·public contract·비가역 변경이 없으면
plan-verify도 자동 생략한다. 사용자에게 생략 여부나 진행 여부를 묻지 않고 구현으로
이어간다. 사용자가 plan 검증을 명시 요청하면 이 생략 조건보다 명시 요청이 우선한다.

## 사전 조건

- `Test-Path <plan_root>/<slug>.md` ✅
- plan frontmatter status=approved
- `py -3 <methodos_root>/hooks/common/plan_preflight.py <plan_root>/<slug>.md --repo <project_root>` PASS. FAIL은 reviewer dispatch 전 planner가 고치며 attempt를 소모하지 않는다.

## 산출 artifact (강제,  Phase 2 D13)

`<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json` (C≥1, N=1, 2, 3) — 필수 필드:
- `kind`: "plan-verify"
- `approved_plan_revision`: 같은 lineage를 식별하는 사용자 승인 SHA
- `candidate_sha` / `parent_candidate_sha`: 이번 plan blob SHA와 직전 attempt의 blob SHA
- `review_scope`: `full` / `scoped`
- `reviewer_provider` / `reviewer_transport`: 실제 실행 provider와 transport
- `reviewer_model` / `reviewer_reasoning_effort`: 실제 값. runtime이 상속값을
  노출하지 않는 local full은 `inherited_from_parent`
- `reviewer_session_id`: Pro 성공 시 ChatGPT session id, local이면 null
- `fallback_reason`: shared schema 호환 필드. Codex route는 자동 fallback이 없으므로 null
- `attempt`: 1, 2, 또는 3 (D13 N=3 한계, 벤치마크 차용 후속)
- `status`: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- `evidence`: 최소 1개 (검증 명령 + 출력 인용)
- `issues`: stable `issue_id` + critical / important / minor + `repeated_from_attempt` (이전 attempt에서 본 issue면 N 명시)
- `escalation_required` / `escalation_reason`
- `self_review`: 4차원
- `reviewer_mode`: `fresh_web_session` | `fresh_subagent` | `controller_self_review` | `unavailable`
- `reviewer_role`: `plan-verify-reviewer` | `none`
- `downgrade_reason`: fresh reviewer를 쓰지 않았을 때만 필수

**자동 수정 흐름** (N=3, 벤치마크 차용):
- attempt N BLOCKED → plan SKILL이 conv로 자동 수정 → attempt N+1
- attempt 3도 BLOCKED 또는 `repeated_from_attempt`로 동일 critical issue 재등장 → `escalation_required: true` + 사용자 escalate
- 사용자에겐 *기술 세부 X* — 남은 사용자 체감 시나리오/결정 필요 여부만
- `user_facing_escalation`을 만들 때 `blocked_scenarios`와 `decision_options`는 쉬운 말로 쓴다. 금지: internal file graph, reviewer jargon, verification type, schema field 이름만 던지기. 허용: "이 선택을 하면 기존 저장값을 덮을 수 있어요", "이 선택은 안전하지만 결과가 적게 나올 수 있어요".

**lineage·review scope·route**:
- 같은 `approved_plan_revision` 안에서 BLOCKED issue를 고친 plan blob chain만 같은 lineage다. 새 approved revision 또는 사용자 결정으로 시작한 새 cycle은 attempt 1의 새 lineage다.
- attempt 1만 class-appropriate baseline full review다. attempt M+1은 fresh scoped reverify이며 stable prior issue, fix delta/changed paths, 영향받은 contract·caller·decision graph와 selector만 검증한다. unchanged contract 안의 새 issue도 scoped 안에서 처리한다.
- full reverify는 acceptance/oracle 변경, public/caller/decision graph 변경, out-of-scope touch, selector로 닫히지 않는 shared output, impact radius 미폐쇄일 때만 허용하고 `escalation_reason`에 predicate를 기록한다. attempt 증가나 unchanged contract의 새 issue는 full 사유가 아니다.
- scoped reviewer가 위 predicate로 `NEEDS_CONTEXT`를 반환하면 그 응답은 routing
  envelope이며 terminal artifact로 저장하지 않는다. 같은 attempt/candidate/parent를 유지해 full route로
  재dispatch하고 full 결과 하나만 저장한다. 다른 `NEEDS_CONTEXT`는 terminal이다.
- dispatch 직전 nearest `AGENTS.md`가 지시한 project machine route가 있으면
  point-of-use로 다시 읽는다. 외부 provider route는 현재 사용자의 명시 요청이 있을
  때만 쓴다. 기본 full은 `model`/`model_reasoning_effort`를 생략한 fresh
  `plan-verify-reviewer`가 부모 세션 값을 상속한다. scoped는
  `plan-verify-scoped-reviewer(gpt-5.6-sol/medium)`을 쓴다.
- full prompt에는 canonical reviewer prompt, plan packet, candidate refs, 필요한
  ADR/source와 fresh machine evidence를 self-contained하게 붙인다. local reviewer를
  실행할 수 없거나 packet이 부족하면 외부 provider로 fallback하지 않고
  `NEEDS_CONTEXT`로 닫는다.
- 사용자가 Pro/Claude 검토를 명시하면 해당 provider의 session/model/finality 계약을
  point-of-use로 읽고 별도 fresh review로 실행한다. 그 실패도 자동 fallback 사유가
  아니다. 직전 reviewer의 model/effort는 상속하지 않는다.
- 영속 artifact는 이전 issue의 메모리일 뿐 해소 증거가 아니다. 수정본과 이번 reviewer가 실행한 출력으로 직접 판정한다.

**DONE baseline amendment**:
- amendment를 승인하면 `approved_plan_revision`을 갱신하고 새 lineage attempt 1 full로 시작한다. repair attempt artifact나 scoped repair profile을 재사용하지 않는다.

## 절차 (얇음)

1. **preflight + 범위·route 결정**: preflight PASS를 evidence로 기록한다. 새 lineage attempt 1이면 전체를 읽고, 같은 lineage의 BLOCKED fix attempt M+1이면 scope+delta만 읽는다. full 승격 predicate를 충족한 경우만 baseline 전체를 읽는다. dispatch 직전 project machine route 또는 위 Codex 기본 route를 다시 읽는다.
   - full과 scoped 모두 Codex custom subagent role을 사용하고 `wait_agent`로 완료를
     회수한다. full profile은 부모 model/effort를 상속하고 scoped profile은
     Sol/medium을 명시한다.
   - local subagent를 실행할 수 없으면 `reviewer_mode=unavailable`,
     `downgrade_reason`을 기록하고 `NEEDS_CONTEXT`로 닫는다. controller self-review와
     자동 외부 fallback은 gate를 충족하지 않는다.
   - reviewer 여부를 기록하지 않은 상태로 DONE/DONE_WITH_CONCERNS를 쓰지 않는다.
2. ***적대적 검증* (격리 부재를 외부 자료 대조로 보완)** — 다음 4 차원 모두 점검:
   - **A. 과거 결정 충돌**: `Select-String -Path docs/adr/ -Pattern '<유사 키워드>'`. 충돌 결정 발견 시 issues.critical.
   - **B. decision [0]~[3J] 정합성**: decision-reviewer output이 있으면 [0]/[1A]/[1B]/[3H]/[3J]을 재심하지 말고 그 finding의 해소만 직접 확인한다. 없으면 전체를 walk한다. [1C]/[1D]/[2H]/[3I]는 항상 직접 담당한다. (크기·응집 분해·명시 요청은 [0]/[3J] 위반 아님)
   - **C. 사용자 글로벌 룰** (`~/.codex/AGENTS.md`): 한국어·기술 용어 괄호·체감 시나리오 기술 위반?
   - **D. plan 자체 정합성 + 재사용 계약 실재**: 슬라이스 의존성 순환? touched_files 겹침? estimated_minutes 합리적? **(조건부) plan이 *기존 코드를 재사용/가정*하는 자리("reuse X", "call Y", "기존 Z 그대로")마다 실코드 grep → 실재 + 시그니처/필드 일치 확인.** 불일치(가정한 함수·필드·계약 부재/상이) → critical/important — 허구 계약 위 슬라이스(impl-verify서 튕겨 헛구현). 재사용 없으면(greenfield) skip. 존재·시그니처만 — 코드 품질은 impl-verify 영역.
3. **Evidence 강제** ([2J]):
   - 각 issue마다 `where` (file:line) + `recommend` (수정 방향)
   - *주관 평가 금지* — 측정 가능 근거 인용
4. **자기 점검** (Self-review 4차원):
   - Completeness / Quality / Discipline / Testing
5. **JSON 저장**: `<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json`. lazy 생성. plan frontmatter `verify_attempt` 카운터 동기화.
6. **status 결정**:
   - critical 0 + important 0 → DONE
   - critical 0 + important ≥ 1 → DONE_WITH_CONCERNS
   - critical ≥ 1 → BLOCKED
   - 정보 부족 → NEEDS_CONTEXT

## 적대성 정신

fresh subagent를 쓸 수 있으면 그것이 기본이다. controller self-review로 강등된 경우에만 *외부 자료 4 차원 대조*로 적대성 확보 + reviewer 정신을 보완한다:

> **"Do not trust the report. Verify by reading [the plan], not by trusting [the planner's claims]."** plan 작성자의 "이 정도면 됐다" 주장은 evidence 아님 — 4 차원 대조가 evidence.

→ 위 4 차원 대조가 "메인 컨트롤러 자기 점검"으로 *놓칠* 자리를 잡는다.

## 안 하는 것 (Red Flags)

- 추상 통과 ("괜찮아 보임", "should be fine") — 모든 issue *원문 인용*
- evidence 빈 채 DONE 기재 ([2J] 위반)
- **미실행 명령을 evidence에 기재** — "Report only what was actually verified" 위반 — 이 스킬의 Evidence 규칙 위반
- plan 본문 *수정* (검증자는 read-only)
- "Should I proceed?" 중간 확인 — 자동 진행

## Reeval

- sycophancy 시나리오 2회 등장 (verify-report DONE인데 실제 결함 발견) → Codex subagent reviewer 기본값 강화 검토
- 4 차원 외 *놓친 차원* 발견 → 본문 확장
- 차원 D 재사용 계약 reality-check가 *false positive*(plan이 별칭·paste로 표현해 grep 실패) 잦으면 → 표현 규약 강화 또는 조건 축소. greenfield 위주라 6개월 0회 발동이면 제거 검토 (누적 방지)

---

## 결정 신호


- 4 차원 verdict 직전 → [2J] Evidence (격리 검증 + 명령 출력 직접 인용)
