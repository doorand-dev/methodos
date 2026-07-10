---
name: plan
description: |
  Take an approved spec (or a rough goal) and synthesize an *implementable, slice-by-slice plan* — for each slice, pin the files touched, function signatures, verification method, user-decision slots (M1), and changes vs the approved version (M2). Signatures/schemas go inline in the plan body.
  **Self-trigger (no router)**: right after a spec (`docs/specs/slug.md`) is approved, or when multi-slice non-trivial work is *about to be implemented*. "plan", "계획 짜", "PRD 작성", "기능 분해".
  **Standalone — user decision space**. Takes spec.md as input and synthesizes *without further interview*. Output `.claude/plans/slug.md`; after approval, proceed to model-driven autonomous drive.
  **right-sizing (OPEN)**: slice thickness and whether a P0 spike is needed are *model judgment* by situation (not a rigid rule, FORCE/OPEN). Explicit: `/plan slug 또는 거친 골`.
---

# /plan — PRD 상세화 (standalone, 사용자 결정 공간)

> **약어 지도** — 이 문서만 읽어도 아래가 그 자리에서 이해되게 한다. ("외부 문서로 넘기기"는 빠져나갈 구멍 — 이 문서는 다른 시기에 홀로 로드된다.)
> - `FORCE` = 슬롯의 *존재*는 강제, 빈 채 통과 금지 / `OPEN` = 그 안의 *값*은 모델이 판단
> - `M1` = 사전에 사용자가 정해야 할 결정 리스트(§7) / `M2` = 승인본 대비 *사용자 체감 변화*만 추려 다시 받는 서사(§11)
> - `G-A` = impl이 슬라이스를 직접 짤지(`inline`) 격리 서브에이전트로 떼어 보낼지(`sdd`) 정하는 결정 / `drive_config` = 그 결정을 plan 단계에 미리 박아두는 자율주행 진입 정책(§ drive_config)
> - `[3H]` = DB→로직→화면을 관통하는, 혼자 작동·검증되는 가장 작은 슬라이스 / `[2J]` = "통과" 단언 전 실제 명령 출력을 직접 인용한다(Evidence) / `[3J]` = 재사용 추출은 두 사용처가 *같은 이유로 함께 변할 때만*
> - 위 한 줄로 평시엔 충분. 원칙 전체를 외부 문서로 떠넘기지 말고, 이 스킬 안의 판단 조건을 우선 적용한다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: spec approved 직후, 또는 다슬라이스 비-trivial 작업 *구현 전*
- 자연어: "plan", "계획 짜", "PRD 작성", "기능 분해"
- 명시: `/plan <slug 또는 거친 골 한 줄>`
- right-sizing(슬라이스 두께·P0 스파이크)은 **OPEN** — 상황으로 모델 판단 (근거 `using-methodos` FORCE/OPEN)

## 모델 사전점검 (합성 *전* 1회 — fable early-nudge)

plan은 *자율 합성*이라 인터뷰 없이 혼자 짠다 — 사람이 중간에 못 잡는다. 그래서 합성 품질이 모델에 직결되고, **fable이 본전 뽑는 첫 자리**가 여기다(자율 단계). 단 fable 추천이 drive_config(=합성 *끝*)에서 처음 뜨면 plan은 이미 현 세션 모델로 합성돼버려 *늦다*. 그래서 **합성 시작 전 1회** 능동 점검:

- spec을 읽고 L-tier 신호(아키텍처 변경 ∨ 결정 ≥5 ∨ overnight 다슬라이스 자율주행 ∨ 보안) 판정.
- **L-tier ∧ 현 세션 model ≠ fable** → 합성 *전* surface (능동 추천, self-anchoring 차단 — opus planner가 자기보다 위 모델을 안 떠올리는 bias):
  > "이 spec L-tier 신호(<근거>). plan 합성은 자율 단계라 fable이 본전. 지금 `/model fable`로 바꾸면 **plan부터** fable로 합성(impl 진입 전까지 model 자유). 안 바꾸면 현 모델로 합성하고 drive_config에서 *impl 컨트롤러만* 따로 escalation."
- **L-tier 아님 ∨ 이미 fable** → nudge 없이 바로 합성.
- grill-me(인터랙티브, 사람=안전망)엔 이 점검 없음 — fable 본전 자리 아님. 자율 단계(plan·impl)만. (근거: 2026-06-10 사용량 실측 + 본전 축 = human-in-loop 유무.)

drive_config(합성 끝)의 controller 불일치 flag는 이 nudge를 *안 받았거나 거절*한 경우의 2차 그물 — impl 드라이브만 커버. 둘은 중복 아니라 **다른 시점**(합성 전 = plan+impl / 합성 끝 = impl만).

## 산출 artifact (강제)

`.claude/plans/<slug>.md` — Markdown frontmatter + body. **plan-verify-reviewer + impl agent가 paste 받음** (sp "Never make subagent read plan file" — 본문 self-contained 필수).

### Frontmatter schema

```yaml
---
slug: <kebab-case>
created_at: YYYY-MM-DD
status: draft | approved
spec_ref: docs/specs/<slug>.md   # grill-me skip 케이스만 null
source_spec:                       # spec 입력 추적
  path: docs/specs/<slug>.md
  approved_at: YYYY-MM-DDTHH:MM:SS+09:00
  sha: <git blob SHA — drift 감지용>
amendment:                         # 이미 DONE인 baseline 보정일 때만
  baseline_status: null | DONE
  scope: []                        # 바뀐 slice ID만; 빈 배열은 최초 plan
approved_plan_revision: <git SHA>  # 사용자 마지막 승인 SHA (M2 diff 기준점)
verify_cycle: 1                    # escalate→user-decision→plan rev = 1 cycle
verify_attempt: 0                  # cycle 내부 0~3 카운터
escalation_reason: null            # N=3 또는 같은 critical 2회 반복 시 한 줄 (매 cycle reset)
goal: <한 문장>
architecture: <2-3 문장>
tech_stack: [..]
slices:
  - id: 1
    title: <한 줄>
    files:
      create: [<exact path>, ..]
      modify: [<exact path>, ..]
      test: [<exact path>, ..]
    verification:
      type: unit_test | command | fixture | artifact | custom
      command: <executable command>
      expected_exit_code: 0
      # type별 추가 필드 — § Verification type enum 참고
    estimated_minutes: <2-30>
    line_budget: <1-200>             # slice의 계획 코드+테스트 총량 상한 (preflight가 강제)
    public_contracts: []             # 바뀌는 public symbol/artifact만
    public_callers: []               # public_contracts가 있으면 caller 전수; 없으면 빈 배열
    # M1 결정 리스트 (사용자 결정 필요 자리만)
    decision_needed: false           # 기본 false (단순 HOW는 AI 결정)
    user_facing_scenario: null       # decision_needed=true일 때 쉬운 용어 시나리오
    recommended: null                # AI 추천
    options: []                      # [{label, consequence}, ..]
self_review:
  coverage_gaps: []
  placeholders_found: []
  type_inconsistencies: []
drive_config:                      # 자율주행 진입 정책 (FORCE 슬롯 · OPEN 값) — § drive_config
  controller:
    model: fable | opus | sonnet   # 자율 baseline. 현 세션 model과 불일치 시 flag (compact는 model 못 바꿈)
    effort: low | medium | high    # fable·opus일 때만 의미. 가장 어려운 슬라이스 기준 *단일값 전구간* (per-slice effort 레버 부재)
  dispatch:                        # 슬라이스별 실행모드 — impl G-A의 provisional 결정 (런타임 이탈 가능)
    - slice: <id>
      mode: inline | sdd
      model: fable | opus | sonnet # sdd일 때만 — dispatched subagent model override
      isolation: null              # 파일 공유 시 worktree
  rationale: <한 줄 — 어느 슬라이스가 어느 knob(model/effort/dispatch)을 강제했나>
---
```

**필드 강제 룰**:
- `spec_ref`: `docs/specs/<slug>.md` 존재해야 함 (grill-me skip 케이스만 null 허용)
- `source_spec.sha`: spec frontmatter SHA — drift 감지 (spec 바뀌면 plan 재합성 필요)
- `amendment`: 이미 DONE인 baseline의 behavior-preserving 내부 보정이면 `baseline_status: DONE` + 바뀐 slice ID만 `scope`에 적는다. source spec, 사용자 체감 동작, 권한·데이터·비가역, public contract, cross-slice ownership을 바꾸면 이 경로를 쓰지 않고 full review다.
- `approved_plan_revision`: 사용자가 명시 승인한 commit SHA. M2 diff 기준점
- `verify_attempt`: 0=초안, 1=plan-verify 1차 후 자동 수정, 2=2차 수정 (N=3 한계)
- `decision_needed`: 판정 기준 — 사용자 체감 분기 / 비가역 / 사용자 자산 영향 중 하나 이상
- `line_budget`: 1~200. 테스트까지 포함해 이 값을 넘길 것 같으면 slice를 나눈다. reviewer가 세는 대신 preflight가 먼저 막는다.
- `public_contracts`/`public_callers`: public symbol·artifact의 동작/시그니처를 바꿀 때만 기재한다. caller를 추측하지 말고 `git grep` 결과를 전수 기록한다. contract만 쓰고 inventory를 빼면 preflight FAIL.
- `drive_config`: status=approved 전 **필수 슬롯**. `dispatch`는 *전 슬라이스* 1:1 `mode`(inline/sdd) 기재(binding). `controller.effort`는 가장 어려운 슬라이스 등급 단일값. *빈 채 approved 금지* ([2J] — impl 자율주행 진입 정책 누락)

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

1. **spec 입력 수신**: `docs/specs/<slug>.md` 읽기. spec status=approved 확인. 없으면(grill-me skip 케이스) 거친 골에서 직접 합성.
   - frontmatter `spec_ref: docs/specs/<slug>.md` 기재
   - spec의 user_stories/out_of_scope/edge_cases/modules를 *입력으로 받음* (추가 인터뷰 없이, to-prd 정신)
   - 충돌 ADR 검색은 spec.md에서 이미 했음 — plan은 *받아 합성*만
   - **novelist preflight (소비자-측 forcing, FORCE)**: spec frontmatter `novelist.required: true && novelist.status != done`이면 **합성 중단** — spec이 실사용 서사 게이트(grill-me §6b)를 안 거친 채 넘어옴. 사용자에게 보고하고 grill-me §6b(spec-novelist 1회 dispatch → fold → `status: done`) 선행 요청. `novelist` 필드 부재(구버전 spec)면 경고만, 진행 허용. (대화 합성 모드가 인터뷰와 novelist를 동반 skip하는 실사용 누락점의 2차 그물 — grill-me의 "인터뷰 skip ≠ novelist skip" 규칙)

2. **File Structure 설계**: task 정의 *전*에 file map 그리기.
   - Create / Modify / Test 라벨 명시
   - 책임 단위 분할 — files that change together live together
   - 기존 컨벤션 따름

3. **슬라이스 분해** ([3H] vertical, thin 우선):
   - DB → 로직 → 화면 관통 줄기
   - 의존성 순서
   - 각 slice = 혼자 작동·검증 가능
   - *thin 우선* — 한 slice가 단독 검증 가능한 관찰 단위보다 크거나 독립 PASS artifact 하나로 설명 불가하면 split
   - **교체 vs 증분 prime** (산입 바이어스 차단): AI는 새것을 *추가*만 하고 그게 대체하는 옛것(죽는 함수·도달 불가 분기·중복 산문)을 잔류시키는 편향이 있다. `files.modify`가 있는 슬라이스마다 *한 번* 자문 — **"이 슬라이스는 기존을 *교체*하나, *증분 추가*하나?"** 교체면 본문 Steps에 *삭제 대상*을 명시 step으로 적어 impl이 추가와 함께 지우게 한다(예: `- [ ] Step N: 옛 update_v1() 및 호출부 제거`). 증분이면 표시 안 함. ***검증 필드 아님*** — plan-time 행동 prime일 뿐(선언된 인식이 있으면 대개 삭제도 따라옴). 선언 안 된 잔재의 사후 catch는 gc 도달성 감사 담당. **의식화 금지** — `files.modify` 없는 순수 create 슬라이스엔 안 물음(routine modify에 빈 자문 남발 X).
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

6. **TDD step-by-step** (5-step, verification.type=unit_test일 때):
   - Write failing test → Run+Verify FAIL → Min impl → Run+Verify PASS → Commit
   - 다른 type은 slice-level verification 1-2 step만

7. **M1 결정 리스트 생성**:

   각 슬라이스 작성 중 *사용자 결정 필요* 자리는 slice frontmatter에 기재:

   ```yaml
   slices:
     - id: N
       ..
       decision_needed: true
       user_facing_scenario: "<쉬운 용어 시나리오>"
       recommended: "<AI 추천>"
       options:
         - {label: "<옵션1>", consequence: "<쉬운 결과>"}
         - {label: "<옵션2>", consequence: "<쉬운 결과>"}
   ```

   **판정 기준** — *하나 이상* 충족 시 `decision_needed: true`:
   - (a) 사용자 체감 시나리오 분기 (사용자가 보는 flow가 갈림)
   - (b) 비가역 (한번 정하면 바꾸기 비쌈)
   - (c) 사용자 자산·권한 영향 (데이터·돈·접근 권한 등)

   *단순 HOW* (라이브러리 선택, 내부 자료구조, 파일 구조)는 `decision_needed: false` — AI 결정.

   **plan 중간 HITL 게이트 신설 금지**: 사전 결정은 M1 `decision_needed`, 사후 검증은 impl-verify-reviewer로 라우팅.

   **spec edge_cases 중복 회피 룰**:
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

8. **Self-Review 3-dim** (by AUTHOR 30초):
   - **Coverage gaps**: spec user_stories 각 요구사항을 슬라이스에 매핑. 빠진 거 명시
   - **Placeholders found**: 본문 grep — "TBD" / "TODO" / "add appropriate" / "similar to slice N" 검출
   - **Type inconsistencies**: signature 이름·인자·반환 타입 슬라이스 간 일치 확인
   - **frontmatter `self_review:` 필드 기재** — 빈 array면 통과, 채워졌으면 fix 후 *다시 셀프 리뷰*. *빈 채로 status=approved 금지* ([2J] Evidence-grade)

8b. **drive_config 합성** (§ drive_config — FORCE 슬롯):

   슬라이스 risk 태그(integration·contract-change·external-I/O·판단) + 두께를 **max() 집계** → controller (model, effort) + 슬라이스별 dispatch(inline/sdd) 산출. frontmatter `drive_config` 기재. rationale 한 줄(어느 슬라이스가 어느 knob을 강제) 필수. **빈 채 다음 단계 금지.**

9. **사용자 검토 1-3턴 + 명시 승인** — status: draft → approved. frontmatter `approved_plan_revision: <SHA>` 기록.
   - 승인 ask에 **drive_config 포함** (M1 결정 리스트와 함께 *세 번째 항목*): dispatch 요약 1줄 + controller (model, effort). `controller.model`이 현 세션 model과 불일치하면 *flag*로 제시 ("이 model로 재기동 / 현 model 수용") — compact·동일세션은 model 못 바꾸므로.

9a. **deterministic preflight** (semantic reviewer 전 강제):

    `py -3 <methodos_root>/hooks/common/plan_preflight.py .claude/plans/<slug>.md --repo <project_root>`를 실행한다. frontmatter/YAML 형태, placeholder, duplicate slice ID, slice/path ownership, PowerShell 명령 문법, source SHA 실제 blob, public caller inventory, line budget을 *먼저* 검사한다.

    - FAIL이면 planner가 기계적으로 고치고 preflight를 다시 실행한다. 이 실패는 semantic reviewer(decision-reviewer/plan-verify) attempt를 소모하지 않는다.
    - PASS 출력은 첫 review artifact의 evidence에 직접 인용한다.
    - reviewer는 Agent 도구로 dispatch하고 그 도구의 정상 반환으로 결과를 직접 회수한다 — artifact watcher·heartbeat polling으로 완료를 판정하지 않는다.

9b. **decision-reviewer 자동 호출** (런타임 tier 값 아니라 *게이트가 직접 관찰하는 상황 신호*로 발동):

    plan status=approved 직후 자동 호출 조건:
    - **보안·권한·공개 계약·사용자 자산·비가역·cross-slice ownership 변경**: 자동 1회
    - **결정 자리 많음**: `decision_needed=true` slice가 ≥2 또는 *비가역/사용자 자산 영향* 결정 있으면 자동 1회
    - `decision_needed=false` + M2 delta 없음 + public behavior/authority/data 변화 없는 behavior-preserving 구조 보정은 **skip**. "architecture change"만으로 호출하지 않는다.
    - skip이면 plan-verify artifact에 위 predicate와 skip 사유를 적는다.

    호출 결과 처리 (공통):
    - status=DONE → 다음 단계 (10. plan-verify)로 넘김
    - status=DONE_WITH_CONCERNS → plan SKILL conv로 issue 반영 → plan-verify로 넘김
    - status=BLOCKED → 사용자 escalate

    사용자 체감: 큰 결정 자리에 "결정 자리 N개라 한 번 더 따져봤어요" 알림 (액션 0).

10. **/plan-verify 자동 트리거 + 자동 수정 conv + cycle 흐름**:

    plan-verify-reviewer agent 격리 검증 → BLOCKED 시 plan SKILL이 conv로 자동 수정:
    - reviewer는 Agent 도구로 dispatch하고 그 도구의 정상 반환으로 결과를 직접 회수한다 — artifact watcher/heartbeat polling을 completion bus로 쓰지 않는다.

    - **N=3 한계** — *최초 approved plan*의 cycle 내부 `verify_attempt` 카운터 frontmatter. 재검증은 issue+delta scoped review다.
    - **cycle 카운터** — escalate→user-decision→plan rev = 1 cycle. `approved_plan_revision` SHA 바뀌면 `verify_cycle += 1`, `verify_attempt = 0`, `escalation_reason = null` reset
    - 각 attempt 산출: `.claude/verify-reports/plan-<slug>-cycle-<C>-attempt-<N>.json`
    - attempt 3 BLOCKED 또는 같은 critical 2회 반복 → escalate. **DONE baseline amendment는 scoped semantic review 1회 + 기계 보정 후 1회까지만; 같은 critical 반복 또는 실제 사용자 결정만 full/escalate**한다.
    - **escalation 표시**: plan-verify-reviewer가 `user_facing_escalation` 필드 생성 (M1 결정 리스트 schema 재사용 — `blocked_scenarios` + `decision_options`). plan SKILL은 *전달만*, 변환 X. 사용자 응답 → slice frontmatter `recommended` 1:1 매핑
    - **자동 재진행**: 사용자 결정 → plan SKILL conv 수정 → plan-verify 자동 재호출 (사용자 명시 명령 X). 새 cycle 시작
    - **Cache 윈도우 5분 유지**: attempt N BLOCKED → 즉시 자동 수정. cycle 사이 사용자 결정 자리만 cache miss 감수 (의도된 trade-off)

    수정 도중 *옵션·임시방편 발화* 감지 시 → `decision` 스킬 자연어 자동 발동 (band-aid 방지).

    사용자 체감: escalate 시 *옵션·결과 같이* 표시 (라운드트립 X). 결정 후 *자동 재진행* — "(다시 검증 중..)" 알림만.

11. **M2 scenario delta approval** (조건부):

    **delta 서사 (inline)**: M2는 diff *제시*(presentation)에 더해, 변화를 **실사용자 시점 delta 서사**로 푼다 — "기존엔 …였는데, 이제 사용자가 …하면 …된다". inline 실행(기계적 SHA diff라 오염 여지 적어 외부 agent 불필요). 이때 *새 보완점*이 잡히면(서사화가 노출) → spec `edge_cases` / plan slice에 fold(presentation-only 아님).

    plan-verify 통과 후 *수정된 최종 plan* vs *사용자 승인 plan* diff 평가:

    - **변화 추출 대상** (사용자 체감만 노출):
      - spec.user_stories 매핑 변화 (어떤 story가 다른 slice로 이동)
      - spec.out_of_scope 변화 (범위 안/밖 변경)
      - spec.edge_cases 매핑 변화 — **그레이존**:
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
    - *체감 변화 없음* → 사용자에게 **한 줄 알림 + escape** (D34):
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

    plan status=approved 후 **모델이 plan-verify → impl(슬라이스별) → impl-verify를 순차 구동**하고, 각 스테이지 경계에서 artifact 흔적(`.claude/verify-reports/*.json` status·`WHY:` commit·`docs/adr/` 존재)을 직접 확인한다 (artifact 계약). 거대 조건문을 생성·복붙하지 않는다.

## drive_config — 자율주행 진입 정책 (FORCE 슬롯 · OPEN 값)

자율주행 impl은 **컨트롤러 모델(controller model)이 시작 시점에 고정**된다 — 도중 전환 불가. 그래서 모델·dispatch 결정을 *plan 단계로 당겨* `drive_config`에 박는다. 안 그러면 impl 진입 때 이 결정이 조용히 누락된다(실측). 값은 모델이 판단하되(OPEN), **슬롯이 비어선 안 된다**(FORCE — 빈 채 approved 금지).

**두 축 비대칭** (effort 레버 부재 — Agent 도구 실측): per-subagent로 제어 가능한 건 `model`(sonnet↔opus↔fable)뿐. 상위 모델 내부 effort(low/med/high)는 *per-slice 레버 없음*. 따라서:
- `controller.effort` = **가장 어려운 슬라이스 기준 단일값, 전구간 동일** (effort 국소화 불가 — 쉬운 슬라이스도 그 등급 과금 감수)
- effort 이질성 복구는 **model 축에서만** — 컨트롤러 하위 등급 + 하드 슬라이스만 상위 모델(opus/fable) dispatch

**fable 기준** (사용량 실측 2026-06-10 — 일괄 승격은 플랜 한도 과소모로 롤백): fable은 *L-tier 장호라이즌 컨트롤러*(아키텍처 리팩터·overnight 다슬라이스 자율주행 — 공식 포지셔닝 long-horizon 최강)와 *아웃라이어 하드 슬라이스 1~2개 sdd dispatch*에만. 고빈도·기계적·scoped 자리(per-slice 검증, attempt 반복)는 opus/sonnet. 2026-06-23부터 fable은 구독 플랜 밖(usage credits 별도 과금) — escalation은 실돈 결정.

**dispatch = binding / controller.model = flag**:
- `dispatch` (슬라이스별 inline/sdd + dispatched `model`) → 세션 내 즉시 적용 (Agent model override는 컨트롤러 model과 무관). plan에 binding.
- `controller.model` → compact·동일세션은 model 못 바꾸니, *현 세션 model과 불일치하면* 사용자 결정 flag ("이 model로 재기동 / 현 model 수용"). 일치하면 자동 확정.

**dispatch 분류** (impl G-A 기준 재사용 — context-locality + coupling + effort-국소화):

| 슬라이스 난이도 분포 | 결합도 | drive_config |
|---|---|---|
| 균일 저위험 | — | controller sonnet, 전부 inline |
| 균일 med/high | — | controller 그 등급, 전부 inline (아웃라이어 없으면 sdd 순손실) |
| 아웃라이어 1~2개 | 느슨(SDD 가능) | controller=쉬운 다수 등급 + 아웃라이어만 상위 모델(opus/fable) sdd |
| 아웃라이어 1~2개 | 빡빡(inline 강제) | 못 떼어 controller=max() 강제 — **rationale에 실토** |

**충돌 tiebreak** (effort-국소화 "sdd" vs 결합도 "inline"): 하드 슬라이스가 *되돌리기 비싼 판단/계약변경*이면 결합 비용 무릅쓰고 **sdd 격리**(fresh 오라클 quarantine — blast-radius 원칙). 빡세지만 기계적이면 inline 유지.

impl의 런타임 G-A는 이 provisional dispatch를 *기본*으로 받되 이탈 가능(OPEN) — 이탈이 blast-radius를 키우면 경고.

## Inline 정책

agent가 plan 받으면 *interface symbol 모른 채* re-derive 부담 → signature·schema는 inline (paste-to-reviewer 같은 세션 모델이라 stale 우려 낮음).

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
- impl-verify-reviewer Stage 1이 plan signature ↔ 실제 commit signature 직접 대조

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

각 slice 1 type 선언. impl-verify-reviewer Stage 1이 type 보고 실행.

| type | command/필드 | expected | 사용 |
|---|---|---|---|
| `unit_test` | `command: pytest tests/../test_X.py -v` | `expected_exit_code: 0` | pure function, schema, parser |
| `command` | `command: <shell cmd>` | `expected_exit_code: 0` + (옵션) `expected_output_contains: ".."` | scripts, integration smoke |
| `fixture` | `command: diff <actual> <expected>` 또는 snapshot tool | `expected_exit_code: 0` | data shape, render output |
| `artifact` | `path: <file>` | `must_exist: true` + (옵션) `must_match: <regex 또는 checksum>` | files, config, migration |
| `visual` | (command 없거나 screenshot/preview) `observe: "<무엇을 육안 확인>"` | 명시 기준 충족 (자율주행 시 스크린샷+비전 — impl-verify G-C) | UI·렌더·대시보드 (테스트 오라클 부재) |
| `custom` | `command: <cmd>` + 자유 평가 룰 | `interpretation: "<통과 기준>"` | 표준 안 맞을 때 escape hatch |

> **impl-verify 오라클 타입(G-B)과 정렬**: 위 type ↔ impl-verify 오라클 택소노미 대응 — `unit_test`↔tdd-parity · `command`↔live-dry-run · `artifact`↔spike-measurement · `visual`↔visual(G-C) · `custom`↔adversarial-review 등. impl-verify가 슬라이스 오라클 타입을 판정할 때 이 `verification.type`을 1차 신호로 읽는다 (두 분류 체계 일치).

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
Select-String -Path .claude/plans/<slug>.md -Pattern 'TBD|TODO|appropriate|similar to|fill in'
# 잡힌 줄 → frontmatter placeholders_found: ["<grep 결과>"]
```

### Type inconsistencies

```
slice 간 cross-grep:
모든 signature 추출 → 함수명·인자 타입·반환 타입 일관성 확인
S2 update_profile() ↔ S3 saveProfile() mismatch → frontmatter type_inconsistencies: ["S2 update_profile() vs S3 saveProfile()"]
```

**룰**: self_review 3 필드 모두 명시. 빈 array면 *통과*, 채워졌으면 fix 후 재self-review까지 status=draft.

## 안 하는 것

- 사용자 추가 인터뷰 (이미 안 것 합성)
- 알고리즘 본체 inline (signature만, /impl이 본체 채움)
- 측정 불가 Goal ("좋은 UX", "사용자 만족" — 측정 가능 형식으로)
- slice 경계 부재 (files.create/modify/test 빈 채 진행)
- self_review 빈 채 status=approved ([2J] 위반)
- drive_config 빈 슬롯(dispatch 미기재) 채 status=approved — impl 자율주행 진입 정책 누락
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
- /plan을 사용자 결정 공간에 둔 게 *사용자 부담* 너무 크면 → 조건부 자율주행 공간 내부 모드 복귀 검토
- **P0 스파이크가 의식화**(불확실성 없는데 P0 남발) 또는 *반대로 한 번도 안 쓰임*(2026-08까지 0회) 발견 시 → 트리거 조건 강화 또는 제거. spike 슬라이스 마커가 실제 필요해지면 schema 필드 1급화 (현재는 prose 표시)
- **drive_config dispatch가 *항상 전부 inline*으로만 나오면**(sdd 한 번도 안 씀, 2026-09까지) → model 축 국소화가 실효 없다는 신호 → 분류 트리거 단순화(controller 단일 선택만 남기고 dispatch 슬롯 제거 검토). 반대로 controller.model flag가 *매번 무시*되면(사용자가 늘 현 세션 수용) → flag 자체 드롭.
- **교체 vs 증분 prime이 의식화**(modify 슬라이스마다 빈 "증분입니다" 남발) 또는 *prime에도 삭제 누락이 그대로*(gc가 잡는 잔재 비율 안 줄어듦, 2026-09까지 무효과) 발견 시 → 제거. prime은 *soft 행동 유도*라 효과 측정 어려움 — 무효·의식화 양방향 다 제거 트리거. catch로 격상하지 않는다.
