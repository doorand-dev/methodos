# Methodos artifact contract + JSON schema

> Methodos 분산 게이트 (grill-me/plan/impl/plan-verify/impl-verify — 중앙 라우터 없음)가 산출하는 *measurable artifact* 표준.
> 모델이 스테이지 경계에서 *artifact 흔적·status*를 직접 확인 (강제력 = 격리 reviewer + 영속 artifact).

---

## Runtime root 해석

아래 표의 `<plan_root>`, `<verify_root>`, `<diagnose_root>`, `<todo_root>`는
계약의 일부다. 각 런타임은 값을 정해 같은 게이트 체인이 같은 artifact를 읽게 해야
한다.

- 프로젝트가 `AGENTS.md`, `CLAUDE.md`, 또는 동등한 런타임 컨텍스트에서 root를
  선언하면 그 값을 우선한다.
- 선언이 없을 때 Claude realization 기본값은 `.claude/plans`,
  `.claude/verify-reports`, `.claude/diagnose-reports`, `.claude/todos.md`다.
- 선언이 없을 때 Codex realization 기본값은 `.Codex/plans`,
  `.Codex/verify-reports`, `.Codex/diagnose-reports`, `.Codex/todos.md`다.
- Claude와 Codex가 같은 프로젝트를 함께 작업하려면 root를 명시적으로 공유
  선언한다. 선언 없이 각 런타임 기본값을 섞으면 artifact가 분리된다.

## 폴더 컨벤션 (사용자 *프로젝트* 폴더 기준)

| 폴더 | 산출자 | 산출 시점 |
|---|---|---|
| `docs/specs/<slug>.md` | `/grill-me` 스킬 (사용자 결정 공간, 명시 실행) | intent 인터뷰 + spec 4-check self-review + user 명시 승인 |
| `<plan_root>/<slug>.md` | `/plan` 스킬 (사용자 결정 공간, 명시 실행) | PRD 상세화 + self-review 3-dim + user 명시 승인 |
| `<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json` | `/plan-verify` 스킬 | plan 격리 검증 끝 |
| `<verify_root>/slice-<N>-attempt-<M>.json` | `/impl-verify` 스킬 (각 슬라이스마다 N=1,2,...; attempt M=1,2,...) | impl 슬라이스 검증 끝 |
| 최종 slice attempt의 `terminal_regression` | goal owner | 최종 candidate SHA의 full regression 1회 또는 `NOT_DECLARED`와 잔여 범위 |
| `<verify_root>/narrative-<slug>-final-attempt-<M>.json` | `impl-novelist` agent | 최종 조립 실물의 full/scoped narrative 검증 끝 |
| `<verify_root>/<review-runtime>-impl-<slug>.json` | 선택적 cross-runtime advisory review | 모든 슬라이스 impl-verify와 최종 novelist 통과 후 1회, loop 없음 |
| `<diagnose_root>/<bug-slug>.md` | 빌트인 `diagnose:` 스킬 | 디버깅 6단계 끝 |
| `<friction_path>` | `blame-code` 스킬 | 교정·코드귀책 발화 자동 또는 수동 `/blame-code` |
| `docs/adr/NNNN-conv-<slug>.md` | `decision` 스킬 | 셀프 수렴 풀 표 결정 |
| `docs/adr/NNNN-why-<slug>.md` | mat pocock 스타일 | 1-3 문장 미니멀 결정 |
| `<runtime_tmp_root>/`, `<runtime_cache_root>/` | (임시) | `.gitignore` 대상 |

**git 추적**: `<plan_root>/`, `<verify_root>/`, `<diagnose_root>/`, `docs/adr/`, `docs/specs/` 모두 *추적*. tmp·cache만 `.gitignore`.

**lazy 생성**: 폴더는 *첫 산출 시* 자동 생성. 미리 만들지 않음.

---

## JSON Schema — plan-decision-review

`<verify_root>/plan-<slug>-decision-attempt-N.json` — `decision-reviewer` agent가 stdout으로 반환하면 controller가 저장.

```json
{
  "schema_version": "1.0",
  "kind": "plan-decision-review",
  "target": "<plan slug>",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "status": "DONE" | "DONE_WITH_CONCERNS" | "BLOCKED" | "NEEDS_CONTEXT",
  "evidence": [
    {"command": "plan section <id> paste", "output_excerpt": "<plan 본문 직접 인용>", "interpretation": "<왜 자문 대상인지>"}
  ],
  "issues": [
    {
      "severity": "critical" | "important" | "minor",
      "where": "<slice id 또는 plan section>",
      "what": "<발견>",
      "principle": "[0]" | "[1A]" | "[1B]" | "[3H]" | "[3J]",
      "alternative": "<대안 또는 옵션 표>",
      "recommend": "<수정 방향 또는 ADR 후보>"
    }
  ],
  "adr_candidates": [
    {
      "slug": "<kebab>",
      "trigger": "<왜 ADR 필요>",
      "options": [{"option": "...", "cost_now": "...", "cost_debt": "...", "reeval": "..."}],
      "recommend": "<권고 옵션 + 이유>"
    }
  ],
  "self_review": {
    "completeness": "<발견>", "quality": "<발견>", "discipline": "<발견>", "testing": "<발견>"
  }
}
```

**drift 방지 룰**: 이 schema가 정본. [agents/claude/decision-reviewer.md](../agents/claude/decision-reviewer.md)의 `<Output_Format>`에 동일 schema가 inline 복제됨 (subagent self-contained context 필요). **schema 변경 시 두 곳 *동시* 갱신**. 변경 추적용 grep 키: `schema_version` 또는 `kind: "plan-decision-review"`.

---

## Spec frontmatter schema

`docs/specs/<slug>.md` — Markdown frontmatter + body. `/grill-me` 산출. `/plan`이 입력으로 받음 (paste-to-sub-skill).

```yaml
---
slug: <kebab>
created_at: YYYY-MM-DD
status: draft | approved   # D14: 2단계만 (3단계 'reviewed' 폭발 회피)
tier: XS | S | M | L       # 선택·서술용 요약 (런타임 값 아님). grill-me 돌면 채울 수 있으나 *어느 게이트도 의존 안 함*. 게이트는 상황 신호로 직접 판단. 임계 근거표 → using-methodos
review:                     # 메타 — frontmatter 상태 폭발 회피
  by: ai | user
  at: YYYY-MM-DDTHH:MM:SS+09:00
  notes: <self-review 한 줄>
goal: <한 문장>
user_stories:
  - {actor: <역할>, feature: <기능>, benefit: <효과>}
out_of_scope: [<항목>, ...]
edge_cases:
  # dry-run friction #3 (2026-05-24) — 결정 자리 명시
  - kind: scenario | decision  # scenario=단순 시나리오 / decision=사용자 결정 가능
    flow: happy | edge
    desc: <한 줄 — 사용자 체감>
    # kind=decision 시 추가 필드:
    decision_status: ai_recommendation_only | user_confirmed
    recommended: <AI 추천>
    options: [<옵션1>, <옵션2>, ...]
modules:
  create: [<이름 + 인터페이스 한 줄>, ...]
  modify: [<이름 + 영향 한 줄>, ...]
testing_priority: [<module name>, ...]
---

# <Feature> Spec
... (Problem / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Edge Cases & Scenarios)
```

### Spec 필드 강제 룰

- `status`: `draft → approved` 단방향 (D14)
- `user_stories`: 최소 1개 (긴 numbered list 권장, to-prd 차용)
- `out_of_scope`: 명시 (빈 배열 OK, 빠지면 X)
- `edge_cases`: 최소 happy 1개 + edge 1개 (D15: stress-test 항상 2개). `kind: decision`은 *plan M1 후보* — `decision_status: user_confirmed`이면 plan M1 skip, `ai_recommendation_only`이면 plan M1에서 한 번 더 confirm (dry-run friction #3/#4)
- `modules.create / modify`: 인터페이스 한 줄만 (코드/파일 경로 inline X, to-prd 정신)
- body는 *self-contained* — `/plan`이 추가 인터뷰 없이 spec만으로 합성

### Drift 동시 갱신 대상

spec schema 변경 시 *반드시 동시 갱신*:
- 본 SKILL-ARTIFACTS.md (정본)
- runtime별 `grill-me/SKILL.md` (spec 산출자)
- (Phase 2) plan/SKILL.md frontmatter `spec_ref` 필드 + plan-verify-reviewer Output_Format

grep 키: `spec_ref` 또는 `kind: "spec"` (있으면)

---

## Plan frontmatter schema

`<plan_root>/<slug>.md` — Markdown frontmatter + body. plan-verify-reviewer + impl agent가 *본문 paste 받음* (self-contained 필수).

```yaml
---
slug: <kebab>
created_at: YYYY-MM-DD
status: draft | approved
tier: XS | S | M | L              # 선택·서술용 요약 (런타임 값 아님). 게이트는 상황 신호로 직접 right-sizing, 이 필드에 의존 안 함
spec_ref: docs/specs/<slug>.md   # D19 — Phase 2 신설. D16 skip 시 null 허용
source_spec:                       # D21 — spec 입력 추적, drift 감지
  path: docs/specs/<slug>.md
  approved_at: YYYY-MM-DDTHH:MM:SS+09:00
  sha: <git blob SHA>
amendment:
  baseline_status: null | DONE
  scope: []                        # DONE baseline 보정 시 바뀐 slice ID만
approved_plan_revision: <git SHA>  # D21 — 사용자 마지막 승인 SHA (M2 diff 기준점)
verify_cycle: 1                    # D36 — escalate→user-decision→plan rev = 1 cycle
verify_attempt: 0                  # D13 — cycle 내부 0~3 카운터
escalation_reason: null            # D13 — N=3 또는 같은 critical 2회 반복 시 한 줄 (매 cycle reset)
goal: <한 문장>
architecture: <2-3 문장>
tech_stack: [...]
slices:
  - id: 1
    title: <한 줄>
    files:
      create: [<exact path>, ...]
      modify: [<exact path>, ...]
      test: [<exact path>, ...]
    verification:
      type: unit_test | command | fixture | artifact | custom
      command: <executable command — type가 cmd 산출일 때>
      expected_exit_code: 0
      # type별 추가 필드:
      # unit_test/command:  expected_output_contains: "..."
      # fixture:            (command이 diff/snapshot)
      # artifact:           path: "<file>", must_exist: true, must_match: "<regex 또는 checksum>"
      # custom:             interpretation: "<통과 기준 한 줄>"
    estimated_minutes: <2-30>
    line_budget: <1-200>           # 코드+테스트 계획량 상한
    public_contracts: []           # public symbol/artifact 변경만
    public_callers: []             # 위 contract의 grep inventory
    # M1 결정 리스트 (D17, Phase 2 신설)
    decision_needed: false           # 기본 false (단순 HOW는 AI 결정)
    user_facing_scenario: null       # decision_needed=true일 때 쉬운 용어 시나리오
    recommended: null                # AI 추천
    options: []                      # [{label, consequence}, ...]
    # hitl/hitl_message 필드 제거됨
self_review:
  coverage_gaps: ["<누락 요구사항 한 줄>", ...]
  placeholders_found: ["<grep 결과>", ...]
  type_inconsistencies: ["<S2 X() vs S3 Y() mismatch>", ...]
---
```

### 필드 강제 룰

- `slug`: kebab-case, 모든 <verify_root>/*-<slug>-* 파일과 공유 키
- `status`: `draft` (작성 중) → `approved` (사용자 명시 승인) 단방향
- `tier`: **선택·서술용 요약** (런타임 값 아님). 게이트는 *상황 신호*(touched·결정·flow·오라클)로 직접 right-sizing하고 이 필드를 *읽지 않는다*. 임계 근거(왜 그 자리에 게이트가 걸리나)는 `using-methodos` tier 표에 있다. 라우터 제거로 "methodos 자동 판정" producer 소멸 → 트리거 조건에 인코딩
- `spec_ref` (D19): `docs/specs/<slug>.md` 존재해야 함. D16 skip 케이스만 null 허용
- `source_spec.sha` (D21): spec git blob SHA — drift 감지. spec 변경되면 plan 재합성 필요
- `amendment`: DONE baseline의 behavior-preserving 내부 보정은 `baseline_status: DONE` + 변경 slice `scope`로 표시하되, 승인 시 `approved_plan_revision`을 갱신하고 새 lineage attempt 1 full review로 시작한다.
- `approved_plan_revision` (D21): 사용자 명시 승인 commit SHA. M2 diff 기준점
- `verify_attempt` (D13): 0/1/2/3 — `plan-verify-attempt-N.json` artifact와 동기화. N=3 후 escalation_reason 필수
- `escalation_reason` (D13): N=3 후에도 BLOCKED 또는 같은 critical issue 2회 반복 시 한 줄
- `slices[].files`: Create/Modify/Test 분리 — sp `writing-plans` 차용. 모든 배열 명시 (빈 배열 OK, 빠지면 X)
- `slices[].verification.type`: 6종 중 하나(unit_test/command/fixture/artifact/visual/custom). 이것은 실행법 메타데이터다. impl-verify는 별도 oracle taxonomy를 만들지 않고 slice에서 `deterministic_artifact_or_command` 또는 `behavior_integration_or_judgment`를 한 번 선택한다.
- `slices[].line_budget`: 1~200. 테스트 포함 예상량이 넘으면 preflight FAIL; slice를 분리한다.
- `slices[].public_contracts`/`public_callers`: public contract 변경 시 caller를 `git grep`으로 전수 inventory한다. contract만 쓰고 inventory를 빼면 preflight FAIL.
- `slices[].decision_needed` (D17): true 시 user_facing_scenario + recommended + options 모두 필수. 판정 기준: 사용자 체감 분기 / 비가역 / 사용자 자산 영향 중 *하나 이상*
- `self_review`: 3 필드 모두 명시. 빈 array면 OK (gap 없음), 채워졌으면 fix 후 *재self-review* 까지 status=draft. **빈 채로 status=approved 금지** ([2J] Evidence-grade)
- body: Goal/Architecture/Tech Stack header + slice별 Files/Decision-encoding/Steps. Decision-encoding inline = signature/schema/test-skeleton만 (algorithm body X)

### Verification type enum 상세

| type | command 패턴 | 측정 |
|---|---|---|
| `unit_test` | `pytest tests/.../test_X.py -v` 또는 `jest ...` | exit 0 + 모든 test pass |
| `command` | 임의 shell cmd | exit 0 + (옵션) output contains |
| `fixture` | `diff <actual> <expected>` | exit 0 (snapshot match) |
| `artifact` | (command 없음) `path: <file>` | file 존재 + (옵션) checksum/regex match |
| `visual` | (command 없거나 screenshot/preview) `observe:` | 명시 기준 충족 — 캡처 경로와 관찰을 evidence에 인용 |
| `custom` | 임의 cmd | `interpretation:` 필드 자유 기준 |

> `unit_test`/`tdd-parity`의 RED→GREEN은 필요한 실행 증거 규칙이다. 다른
> `verification.type` 값은 위 실행법을 제공할 뿐 impl-verify 분류를 추가하지 않는다.

---

## JSON Schema — verify-report (legacy generic 형식)

> 2026-05-23 agent promote 후: 본 generic schema는 *agent 미사용* fallback. agent 산출은 아래 *kind별 specific schema* 4종 사용.

`<verify_root>/plan-<slug>.json` 과 `slice-<N>-attempt-<M>.json` 공통 형식.

```json
{
  "schema_version": "1.0",
  "kind": "plan-verify" | "impl-verify",
  "target": "<plan slug 또는 slice N>",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "status": "DONE" | "DONE_WITH_CONCERNS" | "BLOCKED" | "NEEDS_CONTEXT",
  "evidence": [
    {"command": "<실행 명령>", "output_excerpt": "<출력 핵심 1-3줄>", "interpretation": "<통과·실패 한 줄>"}
  ],
  "issues": [
    {"severity": "critical" | "important" | "minor", "where": "<file:line 또는 섹션>", "what": "<발견>", "recommend": "<수정 방향>"}
  ],
  "touched_files": ["<수정한 파일 경로>"],
  "out_of_slice_touches": ["<슬라이스 외 건드린 파일 — [1C] 신호>"],
  "self_review": {
    "completeness": "<발견>",
    "quality": "<발견>",
    "discipline": "<발견>",
    "testing": "<발견>"
  }
}
```

---

## Agent 산출 4 schema 종합 (2026-05-23 reviewer agent promote, OMC 통합 패턴)

| kind | 산출자 (agent) | model | 저장 경로 | 비고 |
|---|---|---|---|---|
| `plan-decision-review` | [decision-reviewer](../agents/claude/decision-reviewer.md) | opus | `<verify_root>/plan-<slug>-decision-attempt-N.json` | mine [0]~[3J] 적대적 자문 |
| `plan-verify` | [plan-verify-reviewer](../agents/claude/plan-verify-reviewer.md) | runtime route | `<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json` | 4 dimension (A/B/C/D) |
| `impl-verify` | [impl-verify-reviewer](../agents/claude/impl-verify-reviewer.md) | runtime route | `<verify_root>/slice-<N>-attempt-<M>.json` | class-aware Stage 1(spec) + 필요한 Stage 2(quality) 순서 강제 |
| `impl-narrative-final` | [impl-novelist](../agents/claude/impl-novelist.md) | runtime route | `<verify_root>/narrative-<slug>-final-attempt-<M>.json` | assembled implementation의 actor/user-story seam 검증 |

모델은 runtime route가 정한다. Codex 기본 profile은 `runtime-notes/codex.md`가 정본이며 full은 `gpt-5.6-sol/xhigh`, scoped는 `gpt-5.6-sol/medium`이다. 프로젝트 machine route가 있으면 dispatch 직전 point-of-use로 다시 읽고 model/effort를 둘 다 명시한다. 이전 reviewer/controller 값이나 runtime default를 상속하지 않는다.

**cross-runtime advisory review**: 한 런타임의 reviewer들이 같은 모델 가족에 묶일 때만 다른 런타임으로 최종 diff를 1회 적대 검토할 수 있다. 이 review는 Methodos core gate가 아니라 보조 advisory다. 같은 런타임을 다시 호출해 자기검증처럼 쓰지 않는다.

### Runtime impl advisory schema (v1.0)

`<verify_root>/<review-runtime>-impl-<slug>.json` — `/impl` 컨트롤러가 다른 런타임의 최종 diff review를 **foreground+timeout 단일 호출**로 1회 실행하고 결과를 저장한다. Claude에서 Codex companion을 쓰는 경우 기존 파일명은 `<verify_root>/codex-impl-<slug>.json`이고 `kind`는 `"codex-impl"`일 수 있다. Codex runtime은 Codex를 다시 부르지 말고, 별도 reviewer runtime이 있을 때만 이 advisory를 만든다.

- **`base_ref` = plan frontmatter `approved_plan_revision` SHA** (필수). 게이트 시점엔 모든 슬라이스가 커밋돼 working-tree가 비므로 *branch-diff 모드* 강제 — working-tree 리뷰는 "nothing to review"로 빠짐.
- **자리 = 진짜 맨 끝**: (M/L) narrative #4 status DONE 후. advisory review는 loop가 없으므로 코드가 바뀌는 마지막 게이트 뒤라야 *최종 출하 diff*를 본다.
- **foreground 이유**: background 결과 회수는 model-driven 순차 구동엔 결과 회수 행위자가 없어 artifact가 안 써질 수 있다. 1회·맨끝 foreground+bounded timeout 단일 호출이 기본이다.

```json
{
  "schema_version": "1.0",
  "kind": "runtime-impl-advisory | codex-impl",
  "target": "<slug>",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "review_runtime": "<codex | claude | other>",
  "base_ref": "<base SHA 또는 branch>",
  "verdict": "approve | needs-attention | skipped_no_response | error",
  "status": "DONE | DONE_WITH_CONCERNS | SKIPPED",
  "findings": [
    {"severity": "critical | high | medium | low", "file": "<path>", "line_start": 0, "line_end": 0, "confidence": 0.0, "what": "<무엇이 깨지나>", "impact": "<영향>", "recommend": "<수정 방향>"}
  ],
  "fold": {
    "surfaced_to_user": ["<severity ∈ {critical,high} 한 줄>"],
    "todos_appended": ["<medium/low — <todo_root>/todos.md 기재분>"]
  },
  "raw_review": "<codex stdout 원문(markdown) 그대로 — 사람이 골 종료 후 읽음>",
  "evidence": [{"command": "<actual review command>", "output_excerpt": "<review stdout 핵심 발췌>", "interpretation": "<통과/무응답 한 줄>"}]
}
```

**verdict → status 매핑** (모델이 스테이지 경계에서 평가):

| advisory verdict | status | 의미 |
|---|---|---|
| `approve` | DONE | 적대 findings 없음 |
| `needs-attention` | DONE_WITH_CONCERNS | findings 있음 → advisory-fold (차단 X) |
| `skipped_no_response` | SKIPPED | **codex 무응답/empty stdout** — 게이트 통과, 한 줄 알림 |
| `error` | SKIPPED | codex 호출 실패(미설치·timeout 등) — 게이트 통과, 한 줄 알림 |

**stdout 파싱 룰**: reviewer stdout이 렌더된 markdown이면 컨트롤러는:
- `verdict`: stdout에서 `Verdict: (approve|needs-attention)` 한 줄 grep → status 매핑.
- `raw_review`: stdout 원문 markdown 그대로 저장 (사람이 골 종료 후 읽음).
- `findings`/`severity`: markdown의 `- [high|medium|low] ...` 줄에서 best-effort 추출 (codex 출력이 severity 라벨 포함).

**무응답·실패 처리 룰**:
- **무응답/hang** (강제 timeout exit 124) → stdout에 `Verdict:` 줄 없음 → `verdict: "skipped_no_response"` + `status: "SKIPPED"`. ✅ 검증됨 — 루프 안 막힘.
- **호출 실패** (잘못된 base 등, exit≠0, verdict 줄 없음) → `verdict: "error"` + `status: "SKIPPED"`. ✅ 검증됨.
- **빈 diff** (base..HEAD 변경 0) → review 호출 *전* `git diff --shortstat <base>..HEAD` precheck. 비면 호출 생략 + `status: "SKIPPED"`(reason "empty_diff", base 오설정 의심). 빈 diff ≠ "결함 없음".
- 재시도 X (loop 없음). **게이트는 SKIPPED를 통과로 인정** — codex 1회 *시도하고 결과 기록*했으면 충족. codex 응답 *기다리며 model-driven 진행이 멈추는 일 없음*.
- 사용자에겐 한 줄만: "Cross-runtime advisory review 무응답/skip — core Methodos 검증은 이미 통과".

**advisory-fold 룰** (loop X — auto-fix-retry 없음. model-driven 자율주행 공간이라 루프 중 사용자 interaction 아님 — *기록*만):
- `needs-attention` findings 중 **`severity ∈ {critical, high}`** → `fold.surfaced_to_user`에 한 줄씩 (사용자는 *골 종료 후* 읽음 — 루프 중 묻지 않음). (confidence는 보조 — severity 동률 시 높은 confidence 우선.)
- 나머지(medium/low) → `fold.todos_appended` + `<todo_root>/todos.md` append.
- **하드 차단·BLOCKED status 없음** — 새 사용자 round-trip 안 만듦 (메모리 max-autonomy no-new-gates 정합).

**활성화 (단일 predicate — 모든 자리 동일하게)**: **`L tier` 또는 `M tier + D33 충족`**이고 별도 reviewer runtime이 설정돼 있으면 advisory review 1회 실행·artifact 기록. 그 외(M 비-D33/S/XS) 또는 reviewer runtime 부재 시 skip → artifact 미생성.

각 schema 본문은 해당 agent md의 `<Output_Format>` 섹션에 inline. drift 방지 룰: agent md 변경 시 이 SKILL-ARTIFACTS의 schema도 같이 갱신 (또는 그 반대).

### plan-verify schema (kind: "plan-verify", v1.3 — lineage/scoped route)

```json
{
  "schema_version": "1.3",
  "kind": "plan-verify",
  "target": "<plan slug>",
  "cycle": 1,
  "attempt": 1,
  "approved_plan_revision": "<lineage를 식별하는 사용자 승인 SHA>",
  "candidate_sha": "<이번 plan blob SHA>",
  "parent_candidate_sha": null,
  "review_scope": "full | scoped",
  "reviewer_model": "<dispatch에 실제 명시한 model>",
  "reviewer_reasoning_effort": "<dispatch에 실제 명시한 effort>",
  "reviewer_mode": "fresh_subagent | controller_self_review | unavailable",
  "reviewer_role": "plan-verify-reviewer | none",
  "downgrade_reason": null,
  "status": "DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT",
  "evidence": [{"command": "...", "output_excerpt": "...", "interpretation": "..."}],
  "issues": [
    {
      "issue_id": "<stable id>",
      "severity": "critical | important | minor",
      "dimension": "A | B | C | D",
      "where": "<slice id 또는 plan section>",
      "what": "<위반>",
      "reference": "<결정 경로 / 원칙 번호 / 글로벌 룰 / cross-ref>",
      "recommend": "<수정 방향>",
      "repeated_from_attempt": null
    }
  ],
  "escalation_required": false,
  "escalation_reason": null,
  "user_facing_escalation": {
    "blocked_scenarios": ["<체감 한 줄>", "..."],
    "decision_options": [
      {
        "slice_id": 0,
        "scenario": "<사용자 체감 한 줄>",
        "options": [
          {"label": "<옵션1>", "consequence": "<쉬운 결과>"}
        ],
        "recommended": "<옵션 label>"
      }
    ]
  },
  "self_review": {"completeness": "...", "quality": "...", "discipline": "...", "testing": "..."}
}
```

**D35 user_facing_escalation 룰**: reviewer가 기술 issue → 사용자 체감 변환 (M1 결정 리스트 schema 재사용). escalation_required=true일 때만 채움. plan SKILL은 *전달만*, 변환 X.

4 차원: **A** 과거 결정 충돌 / **B** mine 원칙 [0]~[3J] / **C** 사용자 글로벌 룰 / **D** plan 내부 정합성.

**저장 경로** (D36 — cycle 도입): `<verify_root>/plan-<slug>-cycle-<C>-attempt-<N>.json` (C≥1, N=1~3).

**D13 + D36 자동 수정 룰** (N=3 한도, cycle 무한 가능):
- attempt N BLOCKED → plan SKILL이 conv로 수정 → attempt N+1
- attempt 3도 BLOCKED → `escalation_required: true`, `user_facing_escalation` 생성 (D35), 사용자 escalate
- attempt N의 issue가 attempt N-1과 *같은 critical issue* → `repeated_from_attempt: <N-1>` 명시 + 즉시 escalate (N=3 대기 X — persistent fail)
- 사용자 결정 → plan SKILL conv 수정 → `verify_cycle += 1`, `verify_attempt = 0`, `escalation_reason = null` reset → 자동 재호출 (사용자 명시 명령 X, D36)
- 자동 재호출 트리거: `approved_plan_revision` SHA 변경 감지
- 같은 `approved_plan_revision` 안에서 prior issue closure를 위해 이어진 `parent_candidate_sha → candidate_sha` plan blob chain만 같은 lineage다. 새 approved revision/user-decision cycle은 attempt 1의 새 lineage다.
- attempt 1은 `review_scope=full`, `parent_candidate_sha=null`인 유일한 baseline full이다. attempt M+1은 기본 `review_scope=scoped`이고 parent SHA가 직전 artifact candidate와 일치해야 한다.
- attempt M+1의 full은 `escalation_reason`이 `acceptance_or_oracle_changed`, `public_caller_or_decision_graph_changed`, `out_of_scope_touch`, `shared_output_unclosed`, `impact_radius_unclosed` 중 하나일 때만 유효하다. attempt 증가나 unchanged contract 안의 새 issue는 full 사유가 아니다.
- `reviewer_model`/`reviewer_reasoning_effort`는 실제 dispatch 값이다. inherited/default/unknown 값으로 DONE/DONE_WITH_CONCERNS를 쓰지 않는다.

### impl-verify schema (kind: "impl-verify") — class-aware Stage 1/2 (v1.3)

```json
{
  "schema_version": "1.3",
  "kind": "impl-verify",
  "target": "slice-<N>",
  "attempt": 1,
  "approved_plan_revision": "<approved plan SHA>",
  "candidate_sha": "<current candidate SHA>",
  "parent_candidate_sha": null,
  "review_scope": "full | scoped",
  "reviewer_model": "<explicit model>",
  "reviewer_reasoning_effort": "<explicit effort>",
  "verification_class": "deterministic_artifact_or_command | behavior_integration_or_judgment",
  "status": "DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT",
  "stage_results": {
    "spec": "PASS | FAIL | NEEDS_CONTEXT",
    "quality": "PASS | FAIL | NEEDS_CONTEXT | SKIPPED"
  },
  "stage2_skip_reason": null,
  "reviewer_mode": "fresh_subagent",
  "reviewer_role": "impl-verify-reviewer",
  "escalation_required": false,
  "escalation_reason": null,
  "evidence": [{"command": "...", "output_excerpt": "...", "interpretation": "..."}],
  "touched_files": ["<git diff --name-only 결과>"],
  "out_of_slice_touches": ["<slice.touched_files 외 파일>"],
  "issues": [
    {
      "issue_id": "<stable id>",
      "severity": "critical | important | minor",
      "stage": "spec | quality",
      "category": "missing | unrequested | misinterpretation | boundary_violation | intent_overrun | 3I | 3J | 1D | gc-threshold | tdd-red-green | evidence-integrity",
      "where": "<file:line>",
      "what": "<발견>",
      "expected_from_plan": "<plan 기준 — spec stage>",
      "actual_in_code": "<diff 기준 — spec stage>",
      "deletion_test": "<[3I]일 때 — 지우면 어떻게 되나>",
      "recommend": "<수정 방향>",
      "repeated_from_attempt": null
    }
  ],
  "terminal_regression": null,
  "self_review": {"completeness": "...", "quality": "...", "discipline": "...", "testing": "..."}
}
```

`quality=SKIPPED`이면 `stage2_skip_reason`가 비어 있지 않아야 한다. 최종
후보의 마지막 slice artifact만 다음 optional object를 채운다.

```json
{
  "terminal_regression": {
    "candidate_sha": "<HEAD SHA>",
    "owner": "goal_owner",
    "command": "<declared full-regression command or null>",
    "exit_code": 0,
    "output_excerpt": "<actual output or residual scope>",
    "status": "PASS | FAIL | NOT_DECLARED"
  }
}
```

별도 terminal artifact는 만들지 않는다. `terminal_regression`은 goal owner가
최종 candidate SHA에서 한 번만 기록하며, 새 fix로 candidate가 바뀐 경우에만
다시 기록한다.

**저장 경로**: `<verify_root>/slice-<N>-attempt-<M>.json` (M=1~10).

**D24 자동 fix cycle 룰** (N=10):
- attempt M BLOCKED → impl agent가 fix → attempt M+1 (사용자 개입 X)
- attempt 10도 BLOCKED → `escalation_required: true`, `escalation_reason` 명시, 사용자 escalate
- 같은 critical issue 2회 반복 (`repeated_from_attempt: <M-1>`) → 즉시 escalate (intermittent vs persistent 구분, obra 차용)
- **hard ceiling**: attempt 카운터(M=1~10)가 슬라이스 무한 반복을 막는다.

**Stage 순서 강제**: Stage 1이 PASS일 때만 Stage 2를 시작한다. deterministic
data-only에서 source code/abstraction이 없으면 quality는 SKIPPED이며, 그 이유를
기록한다. behavior/integration/judgment attempt 1은 Stage 1+2를 모두 실행한다.

status auto-floor: `intent_overrun` 발견 시 Stage 2 진행하되 status 최소 DONE_WITH_CONCERNS.

---

### drift 방지 룰 (4 schema 공통)

이 SKILL-ARTIFACTS.md가 정본. 각 agent md의 `<Output_Format>`에 동일 schema가 inline 복제됨 (subagent self-contained context 필요). **schema 변경 시 두 곳 *동시* 갱신**. 변경 추적 grep 키: `schema_version` 또는 `kind: "<name>"`.

**필드 강제 (모델이 스테이지 경계에서 평가 가능)**:
- `status`: 4상태 중 하나. 정확히 일치
- `evidence`: DONE/DONE_WITH_CONCERNS는 최소 1개. `output_excerpt` 빈 문자열 금지 (mine [2J] Evidence 위반). reviewer unavailable로 NEEDS_CONTEXT인 impl-verify는 빈 evidence 대신 reason을 남길 수 있다.
- `out_of_slice_touches`: 비어 있어야 [1C] 통과 — 채워져 있으면 *경계 침범 신호*
- `reviewer_mode= fresh_subagent`와 `reviewer_role= impl-verify-reviewer`가 없으면
  DONE/DONE_WITH_CONCERNS를 쓰지 않는다. reviewer dispatch 불가도 `NEEDS_CONTEXT`다.
- `verification_class`는 두 값 중 하나만 허용한다. `stage2_skip_reason` 없는
  `quality=SKIPPED`는 무효다.
- `behavior_integration_or_judgment` attempt 1은 `quality=SKIPPED`일 수 없다.
- 같은 `approved_plan_revision`과 slice에서 prior issue closure를 위해 이어진
  `parent_candidate_sha → candidate_sha`만 같은 candidate lineage다. plan revision이
  바뀌면 attempt 1의 새 lineage로 시작한다.
- attempt 1은 `review_scope=full`, `parent_candidate_sha=null`이다. attempt M+1은
  기본 `review_scope=scoped`이며 parent SHA가 직전 attempt candidate와 일치해야 한다.
- `reviewer_model`과 `reviewer_reasoning_effort`는 dispatch에 실제 명시한 값이다.
  inherited/default/unknown 값으로 DONE/DONE_WITH_CONCERNS를 쓰지 않는다.
- attempt M+1의 `review_scope=full`은 `escalation_reason`이
  `oracle_or_acceptance_changed`, `public_or_caller_graph_changed`,
  `out_of_slice_touch`, `shared_output_unclosed`, `impact_radius_unclosed` 중 하나일
  때만 유효하다.

### impl-narrative-final schema (kind: "impl-narrative-final", v1.1)

```json
{
  "schema_version": "1.1",
  "kind": "impl-narrative-final",
  "target": "<slug>",
  "attempt": 1,
  "approved_plan_revision": "<lineage를 식별하는 사용자 승인 SHA>",
  "base_ref": "<regression base SHA>",
  "candidate_sha": "<assembled implementation HEAD SHA>",
  "parent_candidate_sha": null,
  "review_scope": "full | scoped",
  "reviewer_model": "<dispatch에 실제 명시한 model>",
  "reviewer_reasoning_effort": "<dispatch에 실제 명시한 effort>",
  "status": "DONE | BROKEN | NEEDS_CONTEXT",
  "escalation_required": false,
  "escalation_reason": null,
  "narrative": [
    {"user_story": "<actor/story ref>", "walk": "<first-person prose>", "delivered": true}
  ],
  "evidence": [
    {"command": "<이번 review에서 실행한 cmd>", "output_excerpt": "<1-3 lines>", "interpretation": "<delivered/not>"}
  ],
  "findings": [
    {
      "issue_id": "<stable id>",
      "grade": "broken | regression | deferred_decision | polish",
      "where": "<file:line>",
      "user_story": "<story/success criterion>",
      "what": "<expected vs actual>",
      "route_to": "gate | todos",
      "recommend": "<fix direction>"
    }
  ],
  "self_review": {"completeness": "...", "quality": "...", "discipline": "...", "testing": "..."}
}
```

- 같은 `approved_plan_revision`과 BROKEN fix의 `parent_candidate_sha → candidate_sha` chain만 같은 lineage다. 새 approved revision/user-decision cycle은 attempt 1의 새 lineage다.
- attempt 1은 모든 actor/user_story와 regression 범위를 걷는 `review_scope=full` baseline이다. attempt M+1은 stable prior issue, fix changed paths, 영향받은 actor/entrypoint/flow selector만 fresh scoped reverify한다.
- attempt M+1의 full은 `escalation_reason`이 `acceptance_or_oracle_changed`, `public_caller_or_decision_graph_changed`, `out_of_scope_touch`, `shared_output_unclosed`, `impact_radius_unclosed` 중 하나일 때만 유효하다. attempt 증가나 unchanged contract 안의 새 issue는 full 사유가 아니다.
- DONE은 fresh evidence, closed impact/flow selector, explicit reviewer model/effort가 모두 있어야 한다. inherited/default/unknown 값은 허용하지 않는다.

**Evidence 작성 정본 룰 — OMC `verify` 차용 ("Report only what was actually verified")**:
- `command`에 *실제로 이번 검증 턴에 실행한 명령*만 기재할 것. 과거 출력 재사용·"would run" 미실행 명령 금지
- `output_excerpt`는 *실제 명령 출력에서 직접 발췌*. 모델이 요약·재구성한 문장 금지 (그건 `interpretation` 자리)
- implementer/planner의 "DONE" 보고 자체를 evidence로 인용 금지 — 그건 보고이지 검증 아님 (superpowers `spec-reviewer-prompt.md` "Do not trust the report")
- 양방향 관찰이 필요한 검증(예: regression test red-green)은 *두 방향 명령 출력 모두* evidence에 기재할 것 — 한 방향만으로 "test works" 주장 금지 (superpowers TDD "Watch the test fail")
- caller/producer/consumer/derived-output 중 미확인 항목이 있으면 fail-closed한다.

---

## JSON Schema — plan

`<plan_root>/<slug>.md` (Markdown이지만 frontmatter로 측정 가능 메타):

```markdown
---
slug: <kebab-case 슬라이스 식별자>
created_at: YYYY-MM-DD
status: draft | approved
slices:
  - id: 1
    title: <한 줄>
    touched_files: [<파일 경로 목록>]
    verification: <명령어 또는 산출물 측정>
    estimated_minutes: <2-15>
---

# Background
...

# Slices
...

# Verification (전체)
...
```

**측정 가능 조건 예**:
- `Test-Path <plan_root>/<slug>.md`
- `Select-String -Path <plan_root>/<slug>.md -Pattern '^status: approved' -Quiet`
- `(Select-String -Path <plan_root>/<slug>.md -Pattern '^slug:').Count -eq 1`

---

## JSON Schema — diagnose-report

`<diagnose_root>/<bug-slug>.md`:

```markdown
---
slug: <bug-slug>
created_at: YYYY-MM-DD
status: reproduced | minimised | fixed | regressed
6_stages:
  reproduce: <명령어 또는 단계>
  minimise: <축소된 재현 케이스 path>
  hypothesise: <가설 한 줄>
  instrument: <측정 도구·로그>
  fix: <commit SHA>
  regression_test: <테스트 path>
---

# Bug summary
...
```

**측정 가능 조건**:
- `Test-Path <diagnose_root>/<bug>.md`
- `Select-String -Path <diagnose_root>/<bug>.md -Pattern '^  reproduce:' -Quiet`
- 6_stages 6개 필드 모두 빈 값 아님 → 자동 평가

---

## 스테이지 경계 artifact 체크 (조건문 컴파일 아님)

모델이 각 스테이지 경계에서 아래 흔적의 *존재·status*를 직접 확인하고 다음 스테이지로 진행한다 — 거대 조건문을 *생성하지 않는다*.

- plan-verify attempt JSON `status` ∈ `DONE`/`DONE_WITH_CONCERNS`
- 슬라이스마다 `WHY:` commit 존재
- slice attempt JSON `status` ∈ `DONE`/`DONE_WITH_CONCERNS`
- 골 종료 시 마지막 slice attempt의 `terminal_regression.status`가 `PASS` 또는
  `NOT_DECLARED`이고, 후자는 잔여 범위를 함께 가진다.
- (M/L) latest narrative-final attempt의 `status` DONE
- (L | M+D33) 별도 reviewer runtime이 설정된 경우 runtime advisory JSON 존재
- ADR 존재 (decision 산출 시)

**원칙** ([3I] 코드 자동 가드 promote):
- *파일 존재* (Test-Path) 우선 — 가장 가벼움
- *상태 평가* (ConvertFrom-Json.status) 다음
- *명령 실행* (pytest 등) 최소화 — 비용 큼 (R8)

---

## 검증 표준

각 artifact 산출 시점에 모델이 스테이지 경계에서 평가 가능한지 *자가 점검*:

| 자문 | 통과 |
|---|---|
| `Test-Path <path>`로 측정되나? | ✅ |
| JSON이면 `(Get-Content | ConvertFrom-Json).<field>`로 값 추출 가능? | ✅ |
| Markdown이면 `Select-String -Pattern '<grep 가능 마커>' -Quiet` 통과? | ✅ |
| *주관 평가*("좋다", "충분하다") 필요? | ❌ — *재설계 필요* |
