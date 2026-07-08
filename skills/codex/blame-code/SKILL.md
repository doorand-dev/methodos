---
name: blame-code
description: AI(또는 사람)가 코드/문서를 잘못 읽은 순간을 코드 구조에 귀책시켜 .Codex/friction.md에 한 줄씩 영속 누적. **명시 트리거 전용** — 사용자가 "blame code", "blame-code", "/blame-code", "코드 탓해봐" 라고 직접 말할 때만 발동. 자동 감지 안 함(교정 발화에 무분별 트리거되어 노이즈 누적되는 것 방지). AI 혼란을 코드 결함 신호로 변환하는 3-layer trio의 수집기 — gc(감사)·improve-codebase-architecture(처리)와 연계.
---

# /blame-code (전역 스킬)

어느 워크스페이스에서든 동작. AI 혼란 순간을 *코드 귀책*으로 영속화 — 휘발되던 행동 데이터를 refactor 후보로 변환.

> 관련 결정: `docs/adr/0001-conv-friction-trio.md` (워크스페이스 기준)

## 발동 트리거

| 신호 | 예시 |
|---|---|
| AI 추론 교정 발화 (자동) | "아니 그게 아니라", "잘못 봤어", "이건 X가 아니야", "헛다리 짚었네", "헷갈렸어", "내가 잘못 본 게 아니라 너가 잘못 본 거잖아" |
| 코드 귀책 의도 발화 (자동) | "코드 탓해봐", "코드 잘못이야", "코드 헷갈리게 돼있어", "이거 코드 결함이지", "코드/문서 귀책" |
| 명시 호출 (수동) | `/blame-code` |
| 프로젝트별 보완 | `<workspace>/.Codex/blame-code.toml`의 `extra_triggers` |

자동 감지 시 *바로* 항목 추가하지 말고, 사용자 다음 발화 1턴 기다림 — *왜* 잘못 봤는지 사용자가 부연해줄 가능성. 부연 받고 항목 작성.

## 실행 절차

### 1. 양식 lazy 생성

`<workspace>/.Codex/friction.md` 없으면 헤더·카테고리 enum·`code-clean` 메타 설명·예시 1개 포함해 생성. 이미 있으면 append만.

### 2. 항목 1개 작성

직전 AI 추론 + 사용자 교정 발화 기반:

| 필드 | 내용 |
|---|---|
| `유발 (path:line)` | 오해 유발한 코드/문서 위치. AI가 잘못 본 *실제* 자리. grep 가능 형식 |
| `오해` | AI가 어떻게 잘못 읽었나. *구체* — "X를 Y로 오인" |
| `재발 방지` | 어떻게 고치면 다음에 안 헤맴 (코드 변경 또는 문서 추가) |
| `카테고리` | enum 1개 |
| `code-clean` | `yes` / `no` / `yes-ambiguous` — **3-agent 파이프라인이 자동 판정 (스스로 박지 말 것)** |

번호는 friction.md max+1 (3자리 zero-pad).

### 3. 3-agent 판정 파이프라인 (자기 판정 합리화 차단, ADR 0013)

`code-clean`은 controller(=Codex 본인)가 결정하지 않음 — 격리 agent 3개에 위임.

**dispatch 실재 (FORCE)**: reader×2 + judge는 *반드시* Task로 실제 호출 — 이 대화에
그 3개 Task 호출이 없으면 friction 항목·footer 작성 금지. controller 자가 요약을 reader
요약으로, 자가 판정을 judge verdict로 **위조 금지** (footer 인용 요구만으론 위조를 못 막음 —
호출 실재가 본체. ADR 0013이 막으려던 self-judge 우회가 바로 이 자리).

**Step 3a — reader×2 병렬 호출** (`blame-code-reader` agent, Haiku):
- 두 agent에 *같은* 입력: `유발 (path:line)` + ±15줄 컨텍스트. **원본 misread는 전달하지 않음** (leading 방지).
- 각자 한 줄 요약 반환: `SUMMARY: <verb + object>` 또는 `UNCERTAIN: <reason>`.

**Step 3b — judge 1회 호출** (`blame-code-judge` agent, Haiku):
- 입력: `reader_a` 요약, `reader_b` 요약, `original_misread` (controller가 *지금까지의 대화 맥락에서* 추출한 misread 한 줄).
- 반환: JSON `{ reader_a_equivalent, reader_b_equivalent, verdict, reasoning }`.

**Step 3c — verdict 기재**:
| judge `verdict` | friction.md `code-clean` | 처리 |
|---|---|---|
| `no` | `no` | refactor 후보 (improve-arch가 처리) |
| `yes-ambiguous` | `yes-ambiguous` | minor 기록. 누적 비율 모니터링 |
| `yes` | `yes` | refactor 후보 X. 원본 AI 책임 |

판정 근거 추적성: 항목 footer에 reader 두 요약 + judge `reasoning` 인용 (`<details>` 블록).

**사용자 override 자리**: 자동 판정이 틀렸다고 보면 사용자가 `code-clean` 필드 수동 수정. escape valve는 *봉쇄되지 않음* — 자리만 *발동 시점 사용자 묻기* → *사후 사용자 수정*으로 이동.

**원본 misread 추출 규칙** (controller 책임):
- 직전 사용자 교정 발화 + 그 전 Codex 추론 양쪽을 한 줄로 압축
- 형식: `"<verb> <object>로 오인"` (예: `"validate를 transform으로 오인"`)
- 모호하면 사용자에게 한 줄 확인 (이 경우만 묻기 허용 — judge에 부정확한 misread 넘기면 신호 오염)

### 4. 임계치 surface (가벼움, 한 줄)

추가 후 한 줄:
- 항목 수 > `backlog_limit` (디폴트 20): *"누적 N개. /improve-codebase-architecture로 처리할 시점."*
- `code-clean=yes` 비율 < `code_clean_yes_ratio_min` (디폴트 10%): *"합리화 도구화 패턴 점검 필요 — code-clean=yes가 X%뿐. judge agent 편향 의심."*
- `code-clean=yes-ambiguous` 비율 > 40%: *"judge 동치 판정 모호 빈발 — reader prompt 정밀화 시점."*
- 둘 다 통과: 한 줄 보고 *"friction #NNN 추가 (code-clean=<verdict>). 누적 N개."*

## 카테고리 enum

[1D] 단일 정본 — `.Codex/friction.md` 헤더의 enum 표를 참조. 본 스킬에선 복사 X.

요약: `stale-comment / naming / dead-code / wrong-indirection / missing-docs / duplicate / magic-string / other`.

`other` 누적되면 enum 보완 트리거.

## 연계 (3-layer trio)

| 스킬 | 활성화 시점 | 역할 | friction.md 동작 |
|---|---|---|---|
| `blame-code` (본 스킬) | ms (자동/수동) | 수집 | append |
| `gc` | 분~일 (주기적) | 감사 | 카운트·top 카테고리·`code-clean=yes` 비율 surface |
| `improve-codebase-architecture` (mat) | 의도 발동 | 처리 | Step 1 Explore에서 입력으로 합류 |

활성화 시점이 다른 게 트리오 분리의 근거. 한 스킬로 합치면 모델 깨짐 — `docs/adr/0001-conv-friction-trio.md` 게이트 ④ 참조.

## 항목 처리 라이프사이클

| 단계 | 동작 |
|---|---|
| 추가 | 본 스킬 |
| 잠복 | `code-clean=no` 항목이 friction.md에 누적 |
| 응축 | `/improve-codebase-architecture` grilling으로 distilled rule 도출 → `docs/adr/NNNN-why-<slug>.md` 또는 코드 가드 |
| 제거 | refactor 완료 시 해당 friction 항목 삭제 또는 `resolved: <date>` 한 줄 추가 |

## 안 하는 것

- 자동 refactor 실행 — 본 스킬은 *수집만*. 처리는 improve-codebase-architecture가
- **controller가 `code-clean` 스스로 판정** (자기 판정 = ADR 0013이 차단한 원래 결함). 항상 3-agent 위임
- judge에 *원본 misread 전달 누락* — 그러면 동치 판정 불가 → NEEDS_CONTEXT 회귀
- reader에 *원본 misread 노출* — leading 발생, convergent-error 신호 오염
- friction.md 양식 다른 위치 카피 ([1D] 단일 정본 위반)
- 산출 파일명을 `blame-code.md`로 바꾸기 — `friction.md` 유지

## 프로젝트 보완 (`<workspace>/.Codex/blame-code.toml`, 선택)

toml 없으면 디폴트로 동작. 다음 중 하나라도 필요할 때만 작성:

| 키 | 설명 | 디폴트 |
|----|------|------|
| `extra_triggers` | 프로젝트별 추가 교정·귀책 발화 패턴 (예: `["방향이 틀렸어", "전제가 잘못됐어"]`) | (없음) |
| `extra_categories` | enum에 추가할 카테고리 | (없음) |
| `[thresholds] backlog_limit` | improve-arch 권장 임계치 | `20` |
| `[thresholds] code_clean_yes_ratio_min` | escape valve 모니터링 하한 | `0.10` |

예시:
```toml
extra_triggers = ["방향이 틀렸어", "전제가 잘못됐어"]

[thresholds]
backlog_limit = 30
code_clean_yes_ratio_min = 0.15
```

---

## CONV-GATE 위임

매핑 정본 → [`mine/CONV-GRAPH.md`](../../CONV-GRAPH.md).

- friction.md 기록 직전 → [1C] 누더기 위 누더기 거부 (코드 귀책 합리화 도구화 방지)
- 3-agent 판정 위임 (ADR 0013) → [2J] Evidence (격리 reader + judge 인용)

신규 시점 추가 시 CONV-GRAPH.md 매핑 표 한 줄 갱신.
