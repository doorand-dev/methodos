# mine artifact 컨벤션 + JSON schema

> Methodos 분산 게이트 (grill-me/plan/impl/plan-verify/impl-verify — 중앙 라우터 없음, [ADR 0022](../../../docs/adr/0022-conv-methodos-distributed-gates.md))가 산출하는 *measurable artifact* 표준.
> 모델이 스테이지 경계에서 *artifact 흔적·status*를 직접 확인 (강제력 = 격리 reviewer + 영속 artifact).

---

## 폴더 컨벤션 (사용자 *프로젝트* 폴더 기준)

| 폴더 | 산출자 | 산출 시점 |
|---|---|---|
| `docs/specs/<slug>.md` | `/grill-me` 스킬 (사용자 결정 공간, 명시 실행, [ADR 0006](../../../docs/adr/0006-conv-grill-me-package.md)) | intent 인터뷰 + spec 4-check self-review + user 명시 승인 |
| `.claude/plans/<slug>.md` | `/plan` 스킬 (사용자 결정 공간, 명시 실행, [ADR 0004](../../../docs/adr/0004-conv-plan-outside-goal.md)) | PRD 상세화 + self-review 3-dim + user 명시 승인 |
| `.claude/verify-reports/plan-<slug>.json` | `/plan-verify` 스킬 | plan 격리 검증 끝 |
| `.claude/verify-reports/slice-<N>.json` | `/impl-verify` 스킬 (각 슬라이스마다 N=1,2,...) | impl 슬라이스 검증 끝 |
| `.claude/verify-reports/codex-impl-<slug>.json` | `/impl` 컨트롤러가 `/codex:adversarial-review` 1회 호출 후 stdout 캡처 저장 ([ADR 0016](../../../docs/adr/0016-conv-codex-impl-adversarial-gate.md)) | 모든 슬라이스 impl-verify 통과 후 1회 (L tier, loop X) |
| `.claude/diagnose-reports/<bug-slug>.md` | 빌트인 `diagnose:` 스킬 | 디버깅 6단계 끝 |
| `.claude/friction.md` | `blame-code` 스킬 | 교정·코드귀책 발화 자동 또는 수동 `/blame-code` |
| `docs/adr/NNNN-conv-<slug>.md` | `decision` 스킬 | 셀프 수렴 풀 표 결정 |
| `docs/adr/NNNN-why-<slug>.md` | mat pocock 스타일 | 1-3 문장 미니멀 결정 |
| `.claude/tmp/`, `.claude/cache/` | (임시) | `.gitignore` 대상 |

**git 추적**: `.claude/plans/`, `.claude/verify-reports/`, `.claude/diagnose-reports/`, `docs/adr/`, `docs/specs/` 모두 *추적*. tmp·cache만 `.gitignore`.

**lazy 생성**: 폴더는 *첫 산출 시* 자동 생성. 미리 만들지 않음.

---

## JSON Schema — plan-decision-review

`.claude/verify-reports/plan-<slug>-decision-attempt-N.json` — `decision-reviewer` agent가 stdout으로 반환하면 controller가 저장.

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

**drift 방지 룰**: 이 schema가 정본. [agents/decision-reviewer.md](agents/decision-reviewer.md)의 `<Output_Format>`에 동일 schema가 inline 복제됨 (subagent self-contained context 필요). **schema 변경 시 두 곳 *동시* 갱신**. 변경 추적용 grep 키: `schema_version` 또는 `kind: "plan-decision-review"`.

---

## Spec frontmatter schema (2026-05-24 신설, [ADR 0006](../../../docs/adr/0006-conv-grill-me-package.md))

`docs/specs/<slug>.md` — Markdown frontmatter + body. `/grill-me` 산출. `/plan`이 입력으로 받음 (paste-to-sub-skill).

```yaml
---
slug: <kebab>
created_at: YYYY-MM-DD
status: draft | approved   # D14: 2단계만 (3단계 'reviewed' 폭발 회피)
tier: XS | S | M | L       # 선택·서술용 요약 (런타임 값 아님 — ADR 0022). grill-me 돌면 채울 수 있으나 *어느 게이트도 의존 안 함*. 게이트는 상황 신호로 직접 판단. 임계 근거표 → using-methodos ([ADR 0007])
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
- [grill-me/SKILL.md](grill-me/SKILL.md) (spec 산출자)
- (Phase 2) plan/SKILL.md frontmatter `spec_ref` 필드 + plan-verify-reviewer Output_Format

grep 키: `spec_ref` 또는 `kind: "spec"` (있으면)

---

## Plan frontmatter schema (2026-05-24 갱신, [ADR 0004](../../../docs/adr/0004-conv-plan-outside-goal.md) + [ADR 0006](../../../docs/adr/0006-conv-grill-me-package.md) Phase 2)

`.claude/plans/<slug>.md` — Markdown frontmatter + body. plan-verify-reviewer + impl agent가 *본문 paste 받음* (self-contained 필수).

```yaml
---
slug: <kebab>
created_at: YYYY-MM-DD
status: draft | approved
tier: XS | S | M | L              # 선택·서술용 요약 (런타임 값 아님 — ADR 0022). 게이트는 상황 신호로 직접 right-sizing, 이 필드에 의존 안 함
spec_ref: docs/specs/<slug>.md   # D19 — Phase 2 신설. D16 skip 시 null 허용
source_spec:                       # D21 — spec 입력 추적, drift 감지
  path: docs/specs/<slug>.md
  approved_at: YYYY-MM-DDTHH:MM:SS+09:00
  sha: <git blob SHA>
approved_plan_revision: <git SHA>  # D21 — 사용자 마지막 승인 SHA (M2 diff 기준점)
verify_cycle: 1                    # D36 ADR 0012 — escalate→user-decision→plan rev = 1 cycle
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
    # M1 결정 리스트 (D17, Phase 2 신설)
    decision_needed: false           # 기본 false (단순 HOW는 AI 결정)
    user_facing_scenario: null       # decision_needed=true일 때 쉬운 용어 시나리오
    recommended: null                # AI 추천
    options: []                      # [{label, consequence}, ...]
    # hitl/hitl_message 필드 제거됨 ([ADR 0011](../../../docs/adr/0011-conv-impl-hitl-retraction.md))
self_review:
  coverage_gaps: ["<누락 요구사항 한 줄>", ...]
  placeholders_found: ["<grep 결과>", ...]
  type_inconsistencies: ["<S2 X() vs S3 Y() mismatch>", ...]
---
```

### 필드 강제 룰

- `slug`: kebab-case, 모든 .claude/verify-reports/*-<slug>-* 파일과 공유 키
- `status`: `draft` (작성 중) → `approved` (사용자 명시 승인) 단방향
- `tier`: **선택·서술용 요약** (런타임 값 아님 — [ADR 0022](../../../docs/adr/0022-conv-methodos-distributed-gates.md)). 게이트는 *상황 신호*(touched·결정·flow·오라클)로 직접 right-sizing하고 이 필드를 *읽지 않는다*. 임계 근거(왜 그 자리에 게이트가 걸리나)는 `using-methodos` tier 표([ADR 0007]). 라우터 제거로 "methodos 자동 판정" producer 소멸 → 트리거 조건에 인코딩
- `spec_ref` (D19): `docs/specs/<slug>.md` 존재해야 함. D16 skip 케이스만 null 허용
- `source_spec.sha` (D21): spec git blob SHA — drift 감지. spec 변경되면 plan 재합성 필요
- `approved_plan_revision` (D21): 사용자 명시 승인 commit SHA. M2 diff 기준점
- `verify_attempt` (D13): 0/1/2/3 — `plan-verify-attempt-N.json` artifact와 동기화. N=3 후 escalation_reason 필수
- `escalation_reason` (D13): N=3 후에도 BLOCKED 또는 같은 critical issue 2회 반복 시 한 줄
- `slices[].files`: Create/Modify/Test 분리 — sp `writing-plans` 차용. 모든 배열 명시 (빈 배열 OK, 빠지면 X)
- `slices[].verification.type`: 6종 중 하나(unit_test/command/fixture/artifact/visual/custom). impl-verify-reviewer Stage 1이 type 보고 분기 실행 + 오라클 타입(G-B) 매핑 1차 신호
- `slices[].decision_needed` (D17): true 시 user_facing_scenario + recommended + options 모두 필수. 판정 기준: 사용자 체감 분기 / 비가역 / 사용자 자산 영향 중 *하나 이상*
- `self_review`: 3 필드 모두 명시. 빈 array면 OK (gap 없음), 채워졌으면 fix 후 *재self-review* 까지 status=draft. **빈 채로 status=approved 금지** ([2J] Evidence-grade)
- body: Goal/Architecture/Tech Stack header + slice별 Files/Decision-encoding/Steps. Decision-encoding inline = signature/schema/test-skeleton만 (algorithm body X, [ADR 0004])

### Verification type enum 상세

| type | command 패턴 | 측정 |
|---|---|---|
| `unit_test` | `pytest tests/.../test_X.py -v` 또는 `jest ...` | exit 0 + 모든 test pass |
| `command` | 임의 shell cmd | exit 0 + (옵션) output contains |
| `fixture` | `diff <actual> <expected>` | exit 0 (snapshot match) |
| `artifact` | (command 없음) `path: <file>` | file 존재 + (옵션) checksum/regex match |
| `visual` | (command 없거나 screenshot/preview) `observe:` | 명시 기준 육안 충족 — 자율주행 시 스크린샷+비전(impl-verify G-C), 캡처 경로 evidence 인용 |
| `custom` | 임의 cmd | `interpretation:` 필드 자유 기준 |

> type ↔ impl-verify 오라클 타입(G-B) 정렬: unit_test↔tdd-parity · command↔live-dry-run · artifact↔spike-measurement · `visual`↔visual · custom↔adversarial ([ADR 0022](../../../docs/adr/0022-conv-methodos-distributed-gates.md)).

---

## JSON Schema — verify-report (legacy generic 형식)

> 2026-05-23 agent promote 후: 본 generic schema는 *agent 미사용* fallback. agent 산출은 아래 *kind별 specific schema* 4종 사용.

`.claude/verify-reports/plan-<slug>.json` 과 `slice-<N>.json` 공통 형식.

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

## Agent 산출 3 schema 종합 (2026-05-23 reviewer agent promote, OMC 통합 패턴)

| kind | 산출자 (agent) | model | 저장 경로 | 비고 |
|---|---|---|---|---|
| `plan-decision-review` | [decision-reviewer](agents/decision-reviewer.md) | opus | `.claude/verify-reports/plan-<slug>-decision-attempt-N.json` | mine [0]~[3J] 적대적 자문 |
| `plan-verify` | [plan-verify-reviewer](agents/plan-verify-reviewer.md) | opus | `.claude/verify-reports/plan-<slug>-verify-attempt-N.json` | 4 dimension (A/B/C/D) |
| `impl-verify` | [impl-verify-reviewer](agents/impl-verify-reviewer.md) | opus | `.claude/verify-reports/slice-<N>-attempt-M.json` | OMC code-reviewer 통합 패턴 — Stage 1(spec) + Stage 2(quality) 내부 순서 강제 |

3 reviewer 모두 **opus** (baseline) — OMC analyst/critic/code-reviewer 패턴 정합. 게이트는 고빈도(per-slice × attempt 반복)·scoped라 최상위 모델은 과스펙 — 2026-06-10 fable 일괄 승격이 플랜 한도 과소모로 즉시 롤백된 실측 근거. **fable escalation은 frontmatter가 아니라 호출 시 명시 override**(`Agent(model='fable')` — delegation-enforcer는 명시값 보존): 결정 밀도 높은 L-tier 1회성 자리(decision-reviewer, impl-novelist #4)만. 2026-06-23부터 fable은 구독 플랜 밖(usage credits 별도 과금) — escalation 비용이 실돈. spec stage는 mechanical 비중 크지만 통합 agent로 1 model 단순화 우선.

**cross-model 게이트 추가** ([ADR 0016](../../../docs/adr/0016-conv-codex-impl-adversarial-gate.md)): 위 3종이 전부 Claude 한 가족이라 공유 맹점을 못 잡는 약점을 codex(GPT-5.4)로 보완. agent가 아니라 codex 플러그인 `/codex:adversarial-review` 명령 재사용 (외부 subprocess, Claude 토큰·캐시 안 먹음). 구현 단계 1회·loop X·advisory-fold — 아래 `codex-impl` schema 참고.

### codex-impl schema (kind: "codex-impl", v1.0 — cross-model 적대 게이트, [ADR 0016](../../../docs/adr/0016-conv-codex-impl-adversarial-gate.md))

`.claude/verify-reports/codex-impl-<slug>.json` — `/impl` 컨트롤러가 `/codex:adversarial-review --base <approved_plan_revision> --wait`를 **foreground+timeout 단일 호출**로 1회 실행, stdout(JSON) 캡처해 저장. **agent md inline 복제 없음** (codex 플러그인이 산출자라 mine 측 정본은 이 schema 하나).

- **`base_ref` = plan frontmatter `approved_plan_revision` SHA** (필수). 게이트 시점엔 모든 슬라이스가 커밋돼 working-tree가 비므로 *branch-diff 모드* 강제 — working-tree 리뷰는 "nothing to review"로 빠짐.
- **자리 = 진짜 맨 끝**: (M/L) narrative #4 status DONE 후. codex만 loop 없으니 코드 바뀌는 마지막 게이트 뒤라야 *최종 출하 diff*를 본다.
- **foreground 이유**: `--background` 결과 회수(`/codex:result` polling)는 model-driven 순차 구동엔 background 결과 회수 행위자가 없어 artifact가 안 써짐 → 1회·맨끝 foreground+bounded timeout 단일 호출이 옳음.

```json
{
  "schema_version": "1.0",
  "kind": "codex-impl",
  "target": "<slug>",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "base_ref": "<base SHA 또는 branch>",
  "verdict": "approve | needs-attention | skipped_no_response | error",
  "status": "DONE | DONE_WITH_CONCERNS | SKIPPED",
  "findings": [
    {"severity": "critical | high | medium | low", "file": "<path>", "line_start": 0, "line_end": 0, "confidence": 0.0, "what": "<무엇이 깨지나>", "impact": "<영향>", "recommend": "<수정 방향>"}
  ],
  "fold": {
    "surfaced_to_user": ["<severity ∈ {critical,high} 한 줄>"],
    "todos_appended": ["<medium/low — .claude/todos.md 기재분>"]
  },
  "raw_review": "<codex stdout 원문(markdown) 그대로 — 사람이 골 종료 후 읽음>",
  "evidence": [{"command": "node <plugin>/scripts/codex-companion.mjs adversarial-review --wait --base <approved_plan_revision>", "output_excerpt": "<codex stdout 핵심 발췌>", "interpretation": "<통과/무응답 한 줄>"}]
}
```

**verdict → status 매핑** (모델이 스테이지 경계에서 평가):

| codex verdict | status | 의미 |
|---|---|---|
| `approve` | DONE | 적대 findings 없음 |
| `needs-attention` | DONE_WITH_CONCERNS | findings 있음 → advisory-fold (차단 X) |
| `skipped_no_response` | SKIPPED | **codex 무응답/empty stdout** — 게이트 통과, 한 줄 알림 |
| `error` | SKIPPED | codex 호출 실패(미설치·timeout 등) — 게이트 통과, 한 줄 알림 |

**stdout 파싱 룰 (실측 2026-05-29 smoke test)**: companion `adversarial-review --wait` stdout은 *렌더된 markdown*이지 raw JSON 아님. 컨트롤러는:
- `verdict`: stdout에서 `Verdict: (approve|needs-attention)` 한 줄 grep → status 매핑.
- `raw_review`: stdout 원문 markdown 그대로 저장 (사람이 골 종료 후 읽음).
- `findings`/`severity`: markdown의 `- [high|medium|low] ...` 줄에서 best-effort 추출 (codex 출력이 severity 라벨 포함).

**무응답·실패 처리 룰 (2026-05-29 실측 3케이스 검증)**:
- **무응답/hang** (강제 timeout exit 124) → stdout에 `Verdict:` 줄 없음 → `verdict: "skipped_no_response"` + `status: "SKIPPED"`. ✅ 검증됨 — 루프 안 막힘.
- **호출 실패** (잘못된 base 등, exit≠0, verdict 줄 없음) → `verdict: "error"` + `status: "SKIPPED"`. ✅ 검증됨.
- **빈 diff** (base..HEAD 변경 0) → ⚠️ codex가 **거짓 `approve` 반환**(검증됨). 그대로 믿으면 거짓 DONE → **codex 호출 *전* `git diff --shortstat <base>..HEAD` precheck**. 비면 호출 생략 + `status: "SKIPPED"`(reason "empty_diff", base 오설정 의심). 빈 diff ≠ "결함 없음".
- 재시도 X (loop 없음). **게이트는 SKIPPED를 통과로 인정** — codex 1회 *시도하고 결과 기록*했으면 충족. codex 응답 *기다리며 model-driven 진행이 멈추는 일 없음*.
- 사용자에겐 한 줄만: "Codex 적대 리뷰 무응답/skip — 게이트 통과 (Claude 검증은 이미 통과)".

**advisory-fold 룰** (loop X — auto-fix-retry 없음. model-driven 자율주행 공간이라 루프 중 사용자 interaction 아님 — *기록*만):
- `needs-attention` findings 중 **`severity ∈ {critical, high}`** → `fold.surfaced_to_user`에 한 줄씩 (사용자는 *골 종료 후* 읽음 — 루프 중 묻지 않음). (confidence는 보조 — severity 동률 시 높은 confidence 우선.)
- 나머지(medium/low) → `fold.todos_appended` + `.claude/todos.md` append.
- **하드 차단·BLOCKED status 없음** — 새 사용자 round-trip 안 만듦 (메모리 max-autonomy no-new-gates 정합).

**활성화 (단일 predicate — 모든 자리 동일하게)**: **`L tier` 또는 `M tier + D33 충족`**이면 codex 게이트 활성 → 모델이 codex 1회 실행·artifact 기록. 그 외(M 비-D33/S/XS)는 skip → artifact 미생성. tier표·measurement 조건·최종 체크리스트 *세 곳 모두 이 predicate*로 (smoke test [high] finding 교정 — 자리마다 다르게 쓰면 M+D33 골이 codex 없이 통과).

각 schema 본문은 해당 agent md의 `<Output_Format>` 섹션에 inline. drift 방지 룰: agent md 변경 시 이 SKILL-ARTIFACTS의 schema도 같이 갱신 (또는 그 반대).

### plan-verify schema (kind: "plan-verify", v1.2 — D35/D36 ADR 0012 escalation 정비)

```json
{
  "schema_version": "1.2",
  "kind": "plan-verify",
  "target": "<plan slug>",
  "cycle": 1,
  "attempt": 1,
  "status": "DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT",
  "evidence": [{"command": "...", "output_excerpt": "...", "interpretation": "..."}],
  "issues": [
    {
      "severity": "critical | important | minor",
      "dimension": "A | B | C | D",
      "where": "<slice id 또는 plan section>",
      "what": "<위반>",
      "reference": "<ADR 경로 / 원칙 번호 / 글로벌 룰 / cross-ref>",
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

4 차원: **A** 과거 ADR 충돌 / **B** mine 원칙 [0]~[3J] / **C** 사용자 글로벌 룰 / **D** plan 내부 정합성.

**저장 경로** (D36 ADR 0012 — cycle 도입): `.claude/verify-reports/plan-<slug>-cycle-<C>-attempt-<N>.json` (C≥1, N=1~3).

**D13 + D36 자동 수정 룰** (N=3 한도, cycle 무한 가능, [ADR 0007](../../../docs/adr/0007-conv-tier-and-cache.md)/[ADR 0012](../../../docs/adr/0012-conv-escalation-flow.md)):
- attempt N BLOCKED → plan SKILL이 conv로 수정 → attempt N+1
- attempt 3도 BLOCKED → `escalation_required: true`, `user_facing_escalation` 생성 (D35), 사용자 escalate
- attempt N의 issue가 attempt N-1과 *같은 critical issue* → `repeated_from_attempt: <N-1>` 명시 + 즉시 escalate (N=3 대기 X — persistent fail)
- 사용자 결정 → plan SKILL conv 수정 → `verify_cycle += 1`, `verify_attempt = 0`, `escalation_reason = null` reset → 자동 재호출 (사용자 명시 명령 X, D36)
- 자동 재호출 트리거: `approved_plan_revision` SHA 변경 감지

### impl-verify schema (kind: "impl-verify") — 통합 (Stage 1+2) — D24 ralph 차용 (v1.1, [ADR 0007 후속])

```json
{
  "schema_version": "1.1",
  "kind": "impl-verify",
  "target": "slice-<N>",
  "attempt": 1,
  "status": "DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT",
  "stage_results": {
    "spec": "PASS | FAIL | NEEDS_CONTEXT",
    "quality": "PASS | FAIL | NEEDS_CONTEXT | SKIPPED"
  },
  "escalation_required": false,
  "escalation_reason": null,
  "evidence": [{"command": "...", "output_excerpt": "...", "interpretation": "..."}],
  "touched_files": ["<git diff --name-only 결과>"],
  "out_of_slice_touches": ["<slice.touched_files 외 파일>"],
  "issues": [
    {
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
  "self_review": {"completeness": "...", "quality": "...", "discipline": "...", "testing": "..."}
}
```

**저장 경로**: `.claude/verify-reports/slice-<N>-attempt-<M>.json` (M=1~10).

**D24 ralph 자동 fix cycle 룰** (N=10, [ADR 0007](../../../docs/adr/0007-conv-tier-and-cache.md) 후속 — *model-driven 자율주행 공간* 차용):
- attempt M BLOCKED → impl agent가 fix → attempt M+1 (사용자 개입 X)
- attempt 10도 BLOCKED → `escalation_required: true`, `escalation_reason` 명시, 사용자 escalate
- 같은 critical issue 2회 반복 (`repeated_from_attempt: <M-1>`) → 즉시 escalate (intermittent vs persistent 구분, obra 차용)
- **hard ceiling**: ralph 루프 *내부* attempt 카운터(M=1~10)가 슬라이스 무한 spinning 가드 — 빌트인 turn-limit 의존 없음
- 사용자 의도 "끝까지 자동" 직격 — plan-verify(N=3, 사용자 결정 공간)와 다른 본질

**Stage 순서 강제** (OMC code-reviewer.md L23): Stage 1 critical (`missing` 또는 `boundary_violation`) 발견 시 Stage 2 자동 SKIPPED + 전체 BLOCKED. sp Red Flag "Never start code quality review before spec compliance is ✅" 정신을 *agent 내부 ordering*으로 강제.

status auto-floor: `intent_overrun` 발견 시 Stage 2 진행하되 status 최소 DONE_WITH_CONCERNS.

---

### drift 방지 룰 (3 schema 공통)

이 SKILL-ARTIFACTS.md가 정본. 각 agent md의 `<Output_Format>`에 동일 schema가 inline 복제됨 (subagent self-contained context 필요). **schema 변경 시 두 곳 *동시* 갱신**. 변경 추적 grep 키: `schema_version` 또는 `kind: "<name>"`.

**필드 강제 (모델이 스테이지 경계에서 평가 가능)**:
- `status`: 4상태 중 하나. 정확히 일치
- `evidence`: 최소 1개. `output_excerpt` 빈 문자열 금지 (mine [2J] Evidence 위반)
- `out_of_slice_touches`: 비어 있어야 [1C] 통과 — 채워져 있으면 *경계 침범 신호*

**Evidence 작성 정본 룰 — OMC `verify` 차용 ("Report only what was actually verified")**:
- `command`에 *실제로 이번 검증 턴에 실행한 명령*만 기재할 것. 과거 출력 재사용·"would run" 미실행 명령 금지
- `output_excerpt`는 *실제 명령 출력에서 직접 발췌*. 모델이 요약·재구성한 문장 금지 (그건 `interpretation` 자리)
- implementer/planner의 "DONE" 보고 자체를 evidence로 인용 금지 — 그건 보고이지 검증 아님 (superpowers `spec-reviewer-prompt.md` "Do not trust the report")
- 양방향 관찰이 필요한 검증(예: regression test red-green)은 *두 방향 명령 출력 모두* evidence에 기재할 것 — 한 방향만으로 "test works" 주장 금지 (superpowers TDD "Watch the test fail")

---

## JSON Schema — plan

`.claude/plans/<slug>.md` (Markdown이지만 frontmatter로 측정 가능 메타):

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
- `Test-Path .claude/plans/<slug>.md`
- `Select-String -Path .claude/plans/<slug>.md -Pattern '^status: approved' -Quiet`
- `(Select-String -Path .claude/plans/<slug>.md -Pattern '^slug:').Count -eq 1`

---

## JSON Schema — diagnose-report

`.claude/diagnose-reports/<bug-slug>.md`:

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
- `Test-Path .claude/diagnose-reports/<bug>.md`
- `Select-String -Path .claude/diagnose-reports/<bug>.md -Pattern '^  reproduce:' -Quiet`
- 6_stages 6개 필드 모두 빈 값 아님 → 자동 평가

---

## 스테이지 경계 artifact 체크 (조건문 컴파일 아님)

모델이 각 스테이지 경계에서 아래 흔적의 *존재·status*를 직접 확인하고 다음 스테이지로 진행한다 — 거대 조건문을 *생성하지 않는다* ([ADR 0021](../../docs/adr/0021-conv-goal-demote-router-oracle.md)).

- plan-verify attempt JSON `status` ∈ `DONE`/`DONE_WITH_CONCERNS`
- 슬라이스마다 `WHY:` commit 존재
- slice attempt JSON `status` ∈ `DONE`/`DONE_WITH_CONCERNS`
- (M/L) narrative-final `status` DONE
- (L | M+D33) codex-impl JSON 존재
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
