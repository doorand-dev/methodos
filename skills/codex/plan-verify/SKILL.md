---
name: plan-verify
description: |
  Isolated adversarial verification of a plan (4 dimensions: conflicts with past decisions · decision [0]~[3J] principles · user global rules · plan internal consistency).
  **Self-trigger (no router)**: first approved plan gets one full review. A DONE-baseline amendment gets scoped-delta review by default; promote to full only when its scoped assumptions collapse. "plan 검증", "이 계획 어떻게 보여?", "plan-verify".
  **Evidence (FORCE)**: every issue must *directly quote* command output or file:line — no abstract pass ("looks fine"), no evidence from unrun commands. Output `<verify_root>/plan-slug-verify-attempt-N.json`. Explicit: `/plan-verify slug`.
  **Plain language (FORCE)**: write user escalations not as technical detail but as "what is blocked and what happens if you choose each option", in plain Korean.
---

# /plan-verify — plan 격리 적대적 검증 (얇은 stub)

> *얇은 stub*. Reeval: sycophancy 2회 등장 시 ( 참고).
> Codex에서는 먼저 Codex subagent role을 사용해 fresh reviewer를 띄운다. 사용할 수 없거나 명시적으로 강등하면 그 사유를 artifact에 남긴다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: 최초 status=approved 직후. DONE baseline amendment면 frontmatter `amendment.baseline_status: DONE`와 `scope`로 delta만 읽는다. source spec SHA, user-visible behavior, authority/data, irreversible operation, public contract, cross-slice ownership 중 하나가 바뀌거나 scope 밖 파일/가정이 나오면 full로 승격한다.
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

`decision_needed=false` + M2 delta 없음 + public behavior/authority/data 변화 없는 behavior-preserving 구조 보정은 decision-reviewer skip. 자명한 1-2파일 수정은 둘 다 skip 권장.

## 사전 조건

- `Test-Path <plan_root>/<slug>.md` ✅
- plan frontmatter status=approved
- `py -3 <methodos_root>/hooks/common/plan_preflight.py <plan_root>/<slug>.md --repo <project_root>` PASS. FAIL은 reviewer dispatch 전 planner가 고치며 attempt를 소모하지 않는다.

## 산출 artifact (강제,  Phase 2 D13)

`<verify_root>/plan-<slug>-verify-attempt-<N>.json` (N=1, 2, 3) — 필수 필드:
- `kind`: "plan-verify"
- `attempt`: 1, 2, 또는 3 (D13 N=3 한계, 벤치마크 차용 후속)
- `status`: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- `evidence`: 최소 1개 (검증 명령 + 출력 인용)
- `issues`: critical / important / minor + `repeated_from_attempt` (이전 attempt에서 본 issue면 N 명시)
- `escalation_required` / `escalation_reason`
- `self_review`: 4차원
- `reviewer_mode`: `fresh_subagent` | `controller_self_review` | `unavailable`
- `reviewer_role`: `decision-reviewer` | `plan-verify-reviewer` | `none`
- `downgrade_reason`: fresh reviewer를 쓰지 않았을 때만 필수

**자동 수정 흐름** (N=3, 벤치마크 차용):
- attempt N BLOCKED → plan SKILL이 conv로 자동 수정 → attempt N+1
- attempt 3도 BLOCKED 또는 `repeated_from_attempt`로 동일 critical issue 재등장 → `escalation_required: true` + 사용자 escalate
- 사용자에겐 *기술 세부 X* — 남은 사용자 체감 시나리오/결정 필요 여부만
- `user_facing_escalation`을 만들 때 `blocked_scenarios`와 `decision_options`는 쉬운 말로 쓴다. 금지: internal file graph, reviewer jargon, verification type, schema field 이름만 던지기. 허용: "이 선택을 하면 기존 저장값을 덮을 수 있어요", "이 선택은 안전하지만 결과가 적게 나올 수 있어요".

**scoped re-verify (attempt 2~3)**:
- attempt 1만 plan 전체 fresh 독립 재독. **attempt 2~3은 전체 재독 금지** — 이전 `attempt-N.json`의 `issues`(걸린 것) + plan 수정 delta(diff 또는 변경 슬라이스)만 읽고 "그 issue 해소됐나 + 수정이 새 모순 만들었나" 두 가지로 범위 한정.
- 영속 `attempt-N.json`이 "무엇을 걸었나"의 메모리 — *해소 판정*은 수정본 직접 확인(독립성 유지, JSON 주장 그대로 인용 금지).
- 모델: scoped라 이미 쌈 → opus 유지. 더 짜려면 attempt 2~3만 sonnet 강등 *가능*(옵션).

**DONE baseline amendment**:
- 기본은 baseline 전체가 아니라 `amendment.scope` slice, 해당 path/contract, 그리고 baseline과의 diff만 fresh reviewer에게 paste한다.
- preflight PASS 뒤 semantic reviewer는 1회만 호출한다. 그 reviewer가 찾은 기계 결함은 preflight로 고친 뒤 1회만 scoped re-review한다.
- 동일 critical이 다시 나오거나 사용자 선택이 새로 필요할 때만 full review 또는 사용자 escalate한다. 단순 internal HOW 보정은 full baseline 재독 사유가 아니다.

## 절차 (얇음)

1. **preflight + 범위 결정**: preflight PASS를 evidence로 기록한다. 최초 approved plan이면 전체를 읽고, DONE amendment면 scope+delta만 읽는다. full 승격 predicate를 충족한 경우만 baseline 전체를 읽는다.
   - `decision-reviewer`나 `plan-verify-reviewer`가 필요한 경우, 프로젝트 worker thread가 아니라 Codex subagent role을 사용하고 `wait_agent`로 완료를 회수한다. watcher/heartbeat로 완료를 판정하지 않는다.
   - subagent tool이 없거나 호출하지 않기로 판단하면 `reviewer_mode=controller_self_review` 또는 `unavailable`과 `downgrade_reason`을 artifact에 기록한다.
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
5. **JSON 저장**: `<verify_root>/plan-<slug>-verify-attempt-<N>.json`. lazy 생성. plan frontmatter `verify_attempt` 카운터 동기화.
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
