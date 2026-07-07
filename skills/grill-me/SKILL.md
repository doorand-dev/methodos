---
name: grill-me
description: |
  사용자 의도 정렬 인터뷰 → spec.md — relentless one-Q grill + AI 추천 답안 + codebase grep 우선.
  **자동 발동 (self-trigger, 라우터 없음)**: 신규 기능·비-trivial 작업 의도가 보이고 *아직 코드 작성 전*일 때 — "X 추가하고 싶어"·"Y 구현해줘"·"Z 만들자"·"이 기능 시작"·"새 작업"·"의도 정리"·"그릴미".
  **HARD-GATE (FORCE)**: 신규 기능이 다파일 ∨ 새 schema ∨ 사용자 체감 flow 변화 중 하나라도 동반하면, 코드 전에 *반드시* 이 게이트(intent 정렬 → spec)를 거친다 — 모델의 "바로 코딩" 편향 차단. 산출 `docs/specs/slug.md` status=approved 후 plan으로.
  **발동 안 함**: 작은 수정(touched 1-2 · flow無 · 새 schema無 → 직행) / 이미 spec 확정된 작업 이어받기(해당 스테이지 직행). 명시: `/grill-me slug 또는 거친 골`.
---

# /grill-me — intent 인터뷰 → spec.md

> **약어 지도** — 이 문서는 cross-project 수신자가 raw URL로 가져간다. 맥락을 공유하지 않는 cold reader가 외부 문서 없이 읽게:
> - `to-prd` = 인터뷰 대신 *기존 대화에서 spec을 합성*하는 방식(superpowers 차용) — "이미 충분히 얘기함"이면 질문 0
> - `novelist`/실사용 서사 = fresh-context 에이전트가 *순진한 사용자처럼* 써보며 빈칸을 노출(§3·§6b) / `fold` = 그 결과를 spec에 접어 넣음 / `dispatch` = 격리 서브에이전트로 떼어 보냄
> - `FORCE` = 반드시 거침(HARD-GATE, 빈 채 통과 금지) / `M1`·`M2` = plan 단계의 사용자 결정 리스트·승인본 대비 변화 서사
> - `D12` = 질문 상한 7 디폴트 / `D14` = spec status는 draft·approved 2단계뿐 / `[1D]` = 사실·값은 한 곳에만 (D12·D14 근거는 [ADR 0006](../../../../docs/adr/0006-conv-grill-me-package.md), [1D] 심화는 [decision](../../../skills/decision/SKILL.md))

## 위치 (분산 — 라우터 없음)

| 흐름 | |
|---|---|
| 이전 단계 | **(없음)** — 신규 기능 의도 발화에 *직접 self-trigger* |
| 본 단계 | **grill-me** — intent 정렬 + spec.md 저장 |
| 다음 단계 | `plan <slug>` (spec approved 후 self-trigger — 사용자 명시도 가능) |

사용자 결정 공간. 무게는 *상황 자체 평가*로 정함 (tier 라벨 선언·라우터 전달 X).

## 트리거

### 자동 발동 (self-trigger — description 매칭, 라우터 없음)
- 신규 기능·비-trivial 작업 의도: "X 추가하고 싶어" / "Y 구현해줘" / "Z 만들자" / "이 기능 시작" / "새 작업"
- "grill me" / "의도 정리" / "그릴미"
- **HARD-GATE (FORCE)**: 신규 기능 + (다파일 ∨ 새 schema ∨ 사용자 체감 flow 변화) → 코드 작성 전 *반드시* 발동. 의도가 trivial(아래 skip 조건)이면 강제 아님.

### 명시 호출
- `/grill-me <slug>` — 정해진 slug로 진입
- `/grill-me <거친 골 한 줄>` — slug 자체 결정 후 진입

### 발동하지 않을 때 (skip 조건 — *모두* 충족 시)
- touched_files 예상 1-2개
- 사용자 체감 flow 변화 없음
- 새 schema/API 없음

→ 위 *모두* 충족 시 grill-me skip, 바로 `/plan` 직행 가능.

### 발동하되 인터뷰는 skip — *대화 합성 모드* (to-prd 차용)

위 skip 조건(파일 휴리스틱으로 grill-me *전체* skip)과 별개. 변경 규모는 커도(다파일·복합) **intent가 이미 현재 세션 대화로 확정**된 경우 — 사용자가 사전 대화·dry-run·시나리오 검증을 마치고 grill-me를 호출하는 상황.

- **발동 신호**: 사용자 "이미 충분히 얘기했어" / "dry-run까지 했어" / "인터뷰 말고 정리만" 류, **또는** 현재 대화에서 intent 4축(Purpose / Who / Success / Out-of-scope)이 *모두 도출 가능*
- **동작**: §2 one-Q grill **전체 skip** → 대화·dry-run 결과에서 spec **합성**
- **단 §4 modules confirm + §6b novelist + §7 사용자 review gate는 유지** — to-prd도 modules 확인·spec 승인은 받음. *인터뷰 skip ≠ 무확인*
- **인터뷰 skip ≠ novelist skip** (dogfood 실측 누락점, todo-ctx/008): 대화 합성 모드여도 신규 기능이 다파일 ∨ 다flow면 §6b `spec-novelist` 1회 dispatch는 *그대로 발동*. "사용자와 이미 충분히 얘기함"은 *인터뷰* 면제 근거지 *fresh-context 순진-사용 서사* 면제 근거가 아니다 — 둘은 별개 조건(전자는 intent 도출, 후자는 main-session이 못 보는 빈칸 노출). spec frontmatter `novelist.required:true`면 `status:done` 전엔 plan이 거부(§ plan preflight)
- **dry-run에서 잡은 누락·영향범위는 spec `edge_cases` / `modules.modify`에 박는다** — downstream impl-verify caller-enumeration 게이트(범위 안 caller 누락 검출)가 이 정보를 읽어야 하므로, 대화에만 있고 spec에 없으면 유실됨

## 절차 (7 단계)

### 1. 컨텍스트 탐사 (사용자에게 *안 물음*)

먼저 *자체 grep*:
- `docs/adr/` 유사 slug 검색
- `docs/specs/` 기존 spec 검색
- `CONTEXT.md` / `CONTEXT-MAP.md` 존재 시 도메인 용어
- 최근 git log + touched files
- spec과 충돌하는 기존 ADR 있으면 본문 노출 예정
- **현재 세션 대화·dry-run 결과도 1급 입력** — 이미 확정된 intent·발견한 영향범위는 재질문 X, 그대로 합성 재료 (*대화 합성 모드* 발동 시)

이 단계에서 *이미 안 것*은 사용자에게 묻지 않음.

### 2. one-Q grill — *intent 자리만* (질문 상한 7)

> *대화 합성 모드*(위 발동 조건) 시 이 단계 **전체 skip** — 대화·dry-run에서 intent 4축 직접 채우고 §3로. 인터뷰 0 질문.

질문 영역:
- **Purpose**: 왜 만들어? (1 Q)
- **User perspective**: 누가, 어떤 상황에서 쓰지? (1-2 Q)
- **Success criteria**: 어떻게 "됐다"고 알 수 있지? (1 Q)
- **Out of scope**: 안 하는 건? (1 Q)

**룰**:
- 한 번에 한 질문
- *각 질문에 AI 추천 답안 명시* (사용자가 yes/no/다른 선택)
- **상한 default 7** (codebase/ADR grep으로 답 가능한 건 카운트 X)
- 사용자 "충분" / "그만" 발화 즉시 종료
- 사용자가 답 거부 또는 무응답 시 *AI 추천 채택*
- tech 결정(라이브러리·내부 자료구조·파일 구조)은 *묻지 않음* (AI 합성, /plan에서)

**자동 § 3 전환 신호**:
- intent 4축(Purpose / Who / Success / Out-of-scope) *각자 최소 1 Q 받음* → 자동 § 3 stress-test
- 또는 사용자 "충분" / "그만" 발화 → 즉시 § 3 (남은 영역은 AI 추천 채택)
- 7 Q 상한 도달 → 자동 § 3 (상한 자체가 보호)

**질문 상한 — intent 복잡도로 게이트가 *자체 조절*** (런타임 tier 값 안 받음):
- 자명한 1-2파일 수정·flow無: grill-me 자체 skip (사용자가 직접 수정)
- 단순 intent (목적·성공기준 명확, 옵션 거의 없음): Q ≤ 3 (Purpose 1 + Success 1 + Out-of-scope 1, spec 5 문장)
- 보통: Q ≤ 7 (D12 디폴트, 4축 풀)
- 복합 (아키텍처/보안 ∨ 결정 자리 많음): Q ≤ 7 + decision-reviewer 활성화 (옵션 자리 적대적 자문 자동)
→ 게이트가 *현재 intent의 복잡도를 직접 보고* 상한을 정한다.

### 3. 시나리오 stress-test (항상 최소 2개)

intent 인터뷰 도중·후에:
- **happy path 시나리오** 1개 — 정상 flow 한 줄
- **edge/failure 시나리오** 1개 — 비정상·경계·실패 한 줄

→ AI가 *추천 답과 함께* 제시. 사용자 질문 부담으로 승격 X.

**방향 합의 직후 짧은 서사 흡수** (narrative-dry-run #1): intent 방향이 합의되면 AI가 *혼자* 짧은 실사용 서사를 돌려 미정 자리를 노출 — 결과는 위 stress-test/`edge_cases`로 흘림. 사용자에게 안 물음. (full 서사는 spec 산출 후 #2에서 — 여기선 spec이 아직 없어 축소판.) 정본: `narrative-dry-run.md`.

예:
```
시나리오:
- kind: scenario  / happy / 사용자가 1MB 이미지 업로드 → 자동 압축 후 저장
- kind: decision  / edge  / 사용자가 30MB 이미지 업로드 — 어떻게 처리?
                            recommended: "한도 초과 메시지 + 거부"
                            options: ["거부", "자동 압축 시도 후 안 되면 거부", "강제 압축"]
                            decision_status: ai_recommendation_only
```

**edge_cases 결정 자리 처리 룰**:
- `kind: decision` 자리는 사용자에게 *grill 단계에선 안 물음* — AI 추천만 기재 (`decision_status: ai_recommendation_only`)
- 사용자가 spec 검토 단계에서 명시 confirm 한 자리는 `decision_status: user_confirmed`로 변경
- `decision_status: ai_recommendation_only`인 자리는 *plan M1에서 한 번 더 사용자 confirm*
- `decision_status: user_confirmed`인 자리는 *plan M1 skip* (중복 회피)

도메인 용어 모순 발견 시 *즉시 challenge*:
- "방금 'X' 라고 했는데, 코드는 'Y' 명칭. 어느 게 맞나?"

### 4. modules check-in (인터뷰 X)

이전 단계까지 정리된 intent로 *주요 modules* 제안:
- 어떤 module을 *새로* 만들 것 — 인터페이스 한 줄씩
- 어떤 module을 *수정* — 영향 한 줄씩

사용자에게 yes/no 형식 *confirm* (인터뷰 아님):
- "이 modules 맞나? 빠진 거?"
- "어느 module 테스트 우선?" (1 Q)

### 5. spec.md 저장 — `docs/specs/<slug>.md`

```markdown
---
slug: <kebab>
created_at: YYYY-MM-DD
status: draft  # 2단계만 (draft | approved)
review:        # 메타 — frontmatter 상태 폭발 회피
  by: ai
  at: YYYY-MM-DDTHH:MM:SS+09:00
  notes: <self-review 한 줄>
novelist:      # 실사용 서사 게이트 상태 (artifact forcing — required:true면 status:done 전 approved/plan 진입 금지)
  required: false   # 신규 기능 다파일 ∨ 다flow면 true (§6b 발동 조건과 동일 판정)
  status: pending   # pending | done | skipped  (done=§6b dispatch+fold 완료 / skipped=required:false)
  reason: <한 줄 — required:true 판정 근거 또는 skip 근거>
goal: <한 문장>
user_stories:
  - {actor: <역할>, feature: <기능>, benefit: <효과>}
  - ...
out_of_scope: [<항목>, ...]
edge_cases:
  # 결정 자리는 decision_status 명시 (plan M1 중복 방지)
  - kind: scenario      # 단순 시나리오 (결정 자리 아님)
    flow: happy
    desc: <한 줄>
  - kind: decision      # 사용자 결정 *가능한* 자리
    flow: edge
    desc: <한 줄 — 사용자 체감 시나리오>
    decision_status: ai_recommendation_only   # ai_recommendation_only | user_confirmed
    recommended: <AI 추천>
    options: [<옵션1>, <옵션2>, ...]
modules:
  create: [<이름 + 인터페이스 한 줄>, ...]
  modify: [<이름 + 영향 한 줄>, ...]
testing_priority: [<module name>, ...]
---

# <Feature> Spec

## Problem
<사용자 관점 문제>

## Solution
<사용자 관점 해결>

## User Stories
1. As a <actor>, I want <feature>, so that <benefit>
2. ...

## Implementation Decisions (AI 합성)
- <module/interface/schema 결정 — 파일 경로/코드 X, to-prd 정신>

## Testing Decisions
- 좋은 테스트 = 외부 동작만 검증
- 테스트 우선 module: <list>
- prior art: <기존 유사 테스트 path>

## Out of Scope
- <항목>

## Edge Cases & Scenarios
- happy: <시나리오 한 줄>
- edge:  <시나리오 한 줄>
```

`docs/specs/` 없으면 lazy 생성. **status=draft로 저장**.

### 6. spec self-review (5-check, 인라인 fix)

- **Placeholder scan**: TBD/TODO/incomplete 자리 → 즉시 fix
- **Internal consistency**: 섹션 간 모순? user_stories ↔ Implementation Decisions ↔ Edge Cases
- **Scope check**: 단일 구현 단위로 적정? 너무 크면 decompose 제안
- **Ambiguity check**: 두 해석 가능한 요구사항 → 하나 선택 명시
- **Decision lens** (작성자 자기검열 — reviewer에 미루지 말 것): spec 전체를 decision 렌즈로 1회 훑어 — ⓪ 이 기능/scope 정말 필요한가(불필요하면 줄이거나 멈춤) · 미확정 주장엔 확신도 라벨(확신/추론/모름) · 결정 자리마다 근거 출처(사용자 발화·grep·ADR·명시 가정) 1개. *전문 원칙은 [decision](../../../skills/decision/SKILL.md) 정본* — 여기선 spec-time 단축형만(슬라이스 의존 [3H]·[3J]는 plan decision-reviewer 몫, 여기서 X). 약한 framing(증상-수준 요구·근거 없는 AI 단정·노출 안 된 사용자 체감 분기)은 즉시 `edge_cases`/`user_stories`로 fix.

fix 후 *재 self-review 없음* — 한 번만, 발견되면 인라인 fix하고 진행.

### 6b. spec 실사용 서사 #2 — `spec-novelist` agent (다파일·다flow 기능만)

> 페르소나·자세·산출 형식 정본 = `spec-novelist` agent + `narrative-dry-run.md` #2 (여기 복붙 X, [1D]).

spec self-review 후, **신규 기능이 다파일 ∨ 다flow(복합 실사용 경로)**면 `spec-novelist` agent를 *fresh-context*로 1회 dispatch (자명한 1-2파일·단일 flow는 skip):
- 입력: spec.md *본문 paste*만 (대화 컨텍스트 상속 X — 상속하면 의도된 flow를 narrate해 기법 무력화)
- 산출 `gaps[].proposed_entry` → controller가 spec `user_stories`/`edge_cases`/`modules`에 직접 fold (사용자 추가 질문·게이트 X). `missing_actor`는 `user_stories.add`, ambiguity는 `kind: decision` + `decision_status: ai_recommendation_only`

→ fold 끝난 *enriched spec*을 §7 review gate에 한 번 올림. **승인 게이트 추가 0**.

**frontmatter `novelist` 필드 기입 (artifact forcing — 빠뜨리면 도드라짐)**:
- 다파일 ∨ 다flow 판정 = `novelist.required`. true면 dispatch+fold 후 `status: done`, `reason`에 판정 근거 한 줄.
- 자명한 1-2파일·단일 flow(dispatch skip) → `required: false`, `status: skipped`, `reason`에 skip 근거.
- **이 §6b는 *대화 합성 모드(§ 인터뷰 skip)에서도 동일 발동*** — 인터뷰를 skip해도 novelist는 skip 아님. `required:true`인데 `status:pending`인 채 §7로 못 넘어감(빈 칸이 모델·사용자 양쪽에 보임), plan preflight가 2차 그물.

### 7. 사용자 review gate → status=approved

사용자에게:
```
spec 작성 완료: docs/specs/<slug>.md
검토 부탁드립니다. 변경 사항 있으면 알려주세요.
승인 시 /plan <slug> 호출 — plan은 추가 인터뷰 없이 spec을 입력으로 합성.
```

사용자 명시 승인 → frontmatter `status: draft → approved`.

## CONV-GATE 위임

- intent 인터뷰 도중 *옵션·결정 발화* 감지 시 → `decision` 스킬 자연어 자동 발동
- 사용자 결정 자리(M1) 아직 형식화 안 됨 — *intent 자리만* (Phase 1)
- CONV-GATE mapping is maintained in the private source workspace. In this public package, follow this skill's local trigger and boundary text.

## 안 하는 것

- 사용자 추가 인터뷰 시작 전 컨텍스트 grep 생략 (질문 인플레이션)
- 질문 상한 7개 초과 (D12 — codebase로 답 가능한 건 카운트 X)
- tech 결정 묻기 (라이브러리·내부 자료구조·파일 구조 = AI 합성)
- intent 단계에 옵션 비교 자리 *고의* 생성 — 자연스러운 옵션 발화 시만 decision 자동
- spec status 3단계 (`reviewed` 추가 X — D14)
- spec 본문에 코드/파일 경로 inline (to-prd 정신 — Implementation Decisions는 인터페이스만)
- self-review 재실행 (sp 1회 인라인 fix 패턴)
- `/plan` 자동 invoke (사용자 명시 호출 — ADR 0004)

## 다음 단계

```
status=approved
   ↓ 사용자 명시: /plan <slug>
/plan
   ↓ AI conv (tech 위임) + 결정 리스트 (M1, Phase 2)
   ↓ status=approved
   ↓ /plan-verify 자동 (4-dim 적대적)
   ↓ BLOCKED → plan SKILL 자동 수정 (N=3 한계)
   ↓ scenario delta approval (M2, 조건부)
   ↓ plan status=approved
model-driven 자율주행: 모델이 plan-verify → impl → impl-verify 순차 구동 (artifact 계약 — 거대 조건문 출력 없음)
```

## Reeval

- 질문 상한 7이 *부족·과함* 신호 → 5/9 조정
- stress-test 2개가 *부족·과함* → 케이스별 가변
- skip 조건이 *중요 기능 놓침* 발견 → 강화
- spec self-review 1회가 *놓침 다수* → 2회로 보강
