---
name: impl-verify
description: |
  Isolated 2-stage verification of a slice implementation (spec compliance → code quality) with *built-in* oracle judgment. Borrows the superpowers `subagent-driven-development` pattern.
  **Self-trigger (no router)**: even if the user doesn't know the skill name, fire after a slice commit and before an assertion of "완료/통과/됐어" when no verify artifact covering that slice exists. That artifact may be `slice-N.json` or a batch seam artifact. "impl 검증", "이 구현 어떻게 보여?", "impl-verify".
  **Evidence (FORCE)**: no evidence from unrun commands · no citing the implementer's "DONE" · no pass without enumerating callers.
  **Oracle (G-B, OPEN)**: per slice, judge the oracle *type* (tdd-parity/spike/live-dry-run/visual/adversarial) and choose the verification method — not fixed to a full per-slice reviewer; may downgrade to oracle/self-review/AST0/batch-seam. Output location follows `verify_root` from the nearest `AGENTS.md`/plan convention. The user need not memorize `/impl-verify`; explicit call is optional: `/impl-verify slice N`.
  **Plain language (FORCE)**: write NEEDS_CONTEXT and user-facing surfaces in plain Korean. Instead of "caller impact-radius 미확인", say something like "어디까지 같이 바뀌는지 확인이 안 돼서, 그냥 진행하면 다른 기능이 깨질 수 있어요".
---

# /impl-verify — 슬라이스 구현 검증 gate/controller (얇은 stub)

> *얇은 stub*. Reeval: sycophancy 2회 등장 시.

이 skill이 슬라이스 구현 검증의 실행 지점이다. 별도 gate 참고문서를 만들지 않는다. Fresh reviewer는
이 gate를 만족시키는 기본 수단 중 하나일 뿐이며, 아래 오라클 판정에 따라 controller self-review,
AST0 확인, batch seam verify로 강등할 수 있다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: 슬라이스 commit 직후 "통과" 단언 전, 현재 commit을 덮는 `<verify_root>/slice-<N>-attempt-<M>.json` 또는 batch seam artifact 부재 시
- 자연어: "impl 검증", "이 구현 어떻게 보여?", "impl-verify"
- 명시: `/impl-verify <slice N>`

## 사전 조건

- 해당 슬라이스 commit 존재 (WHY: prefix 있음)
- **하네스 경로 결정**: nearest `AGENTS.md`와 plan frontmatter를 먼저 읽어 `plan_root`와 `verify_root`를 정한다. 예: 프로젝트가 `.claude/plans/`를 정본으로 선언하면 `plan_root=.claude/plans`, `verify_root=.claude/verify-reports`; 별도 선언이 없을 때만 Codex 기본값(`.Codex/plans`, `.Codex/verify-reports`)을 쓴다.
- `Test-Path <plan_root>/<slug>.md` (해당 slice 메타 확인용)
- plan 안 해당 slice의 touched_files 명시되어 있음

## 산출 artifact (강제)

`<verify_root>/slice-<N>-attempt-<M>.json` 또는 batch seam artifact — 필수 필드:
- `kind`: "impl-verify"
- `target`: slice N
- `attempt`: M
- `status`: 4상태
- `evidence`: Stage 1 최소 1개, Stage 2가 실행됐을 때만 Stage 2 최소 1개
- `issues`: severity와 stable issue ID (`ISSUE-...` 또는 프로젝트 기존 ID)
- `touched_files`: 실제 수정 파일 목록
- `out_of_slice_touches`: 빈 배열이어야 [1C] 통과 — 채워져 있으면 BLOCKED
- `self_review`: 4차원
- `reviewer_mode`: `fresh_subagent` | `oracle_downgrade` | `controller_self_review` | `unavailable`
- `reviewer_role`: `impl-verify-reviewer` | `none`
- `downgrade_reason`: fresh reviewer를 쓰지 않았을 때만 필수

## Reviewer dispatch contract

- 기본값은 Codex `impl-verify-reviewer` subagent role이다. 프로젝트 worker thread나 이미 작업 중인 구현 세션을 reviewer로 쓰지 않는다.
- **우선 규칙**: `deterministic_artifact_or_command`와 `behavior_integration_or_judgment`의 attempt 1, 그리고 BLOCKED 뒤의 모든 attempt는 `fresh_subagent` read-only reviewer가 필수다. 이 경우 oracle/self-review/AST0/batch seam 강등은 적용하지 않으며, subagent를 쓸 수 없으면 controller self-review로 DONE을 쓰지 말고 `NEEDS_CONTEXT`로 fail-closed 한다.
- 그 밖의 저위험·미차단 oracle/AST0/batch seam만 fresh reviewer를 쓰지 않을 수 있다. 그때 artifact에 `reviewer_mode`, `reviewer_role`, `downgrade_reason`, 그리고 대신 확인한 evidence를 기록한다.
- reviewer mode를 기록하지 않은 상태로 DONE/DONE_WITH_CONCERNS를 쓰지 않는다.

## 검증 유형 판정 (가장 먼저)

오라클 이름보다 먼저 **무엇을 독립 실행으로 닫을 수 있는가**를 분류한다. 이 분류는 reviewer를 생략하는 허가가 아니다. 어떤 실행을 언제 다시 할지 정하는 비용·정확성 경계다.

| 검증 유형 | 신호 | initial attempt 처리 |
|---|---|---|
| `deterministic_artifact_or_command` | artifact/fixture/hash/schema/정해진 command처럼 같은 입력에서 기계적으로 참·거짓이 나는 계약 | 구현자가 initial commit 전에 **선언한 executable preflight**를 실행·기록한다. 선언에는 command, pass 기준, 확인하는 producer→consumer→derived-output 관계와 가능한 좁은 scope selector를 넣는다. 실패·미선언은 BLOCKED다. attempt 1의 fresh reviewer는 그 출력도 믿지 않고 같은 preflight를 직접 실행한다. |
| `behavior_integration_or_judgment` | public API 동작, caller 조합, 외부 시스템, visual, custom 판단처럼 실행 성공만으로 계약이 닫히지 않는 경우 | slice spec·diff·caller/integration 영향과 해당 targeted check를 fresh reviewer가 직접 검증한다. 테스트가 있어도 이 분류를 자동으로 낮추지 않는다. |

`unit_test`는 닫힌 data 계약만 직접 증명하면 첫 분류에 보조 evidence가 될 수 있지만, public behavior나 caller 조합을 바꾸면 둘째 분류도 함께 적용한다. 애매하면 둘째 분류로 둔다. arbitrary time budget으로 이 판단을 낮추지 않는다.

여러 green 명령을 나열해 artifact 관계가 닫혔다고 추측하지 않는다. 관계 무결성이라면 preflight 하나가 선언된 producer→consumer→derived-output edge를 실제로 따라 대조해야 한다.

구현자는 preflight command/output/exit, coverage, 그리고 commit 전 `git write-tree` 값을 handoff에 기록한다. commit 뒤 controller는 `git rev-parse <HEAD>^{tree}`가 그 값과 같은지 확인해 reviewer input에 paste한다. 이는 provenance이지 reviewer artifact evidence가 아니다. 통과 근거는 fresh reviewer가 이번 attempt에 직접 얻은 출력뿐이다.

## 오라클 판정 (impl-verify 자체 — 라우터 수식자 fold, /)

라우터가 없으므로 이 게이트가 *스스로* 슬라이스 오라클을 판정해 검증법을 고른다 (구 라우터 수식자 fold). **OPEN** — 아래 trade-off를 surface하고 모델이 판단 (rigid rule 아님).

### G-B — per-slice 오라클 *타입* 택소노미 (binary 아님)

슬라이스마다 오라클 *종류*를 판정 → 검증법 도출. 공유 오라클이면 batch.

| 오라클 타입 | 게이트(="됐다") | 검증법 |
|---|---|---|
| `tdd-parity` | pytest green = 끝 | 기존 테스트가 parity → 격리 2-stage 경량(테스트 still green 인용). 진짜 통과 판정 = *오라클 흔적*(green 출력 인용) |
| `spike-measurement` | 수치 보고가 게이트 | 측정값 기록 인용(`.plans/<slug>-spike.md`). 프로덕션 기준(signature·out_of_slice) 면제 |
| `live-dry-run` | 실행 관찰 | 빌트인 `verify`(앱 실행·관찰)로 동작 확인 |
| `visual` (G-C) | UI 육안 | 테스트 오라클 없는 UI → 대시보드/화면 육안 dry-run (빌트인 `verify`/preview 연계) |
| `adversarial-review` | 위험 묶음만 | 동시성·취소·비가역 등 *진짜 위험*에만 적대 리뷰 집중 (전부 말고) |
| (없음) | — | per-slice 격리 2-stage *빡세게* (아래 절차) |

> 입력 신호: plan의 `verification.type`을 1차로 읽어 오라클 타입 매핑(unit_test↔tdd-parity · command↔live-dry-run · artifact↔spike-measurement · `visual`↔visual · custom↔adversarial). plan에 없거나 애매하면 슬라이스 보고 자체 판정.
>
> **visual 오라클 × 자율주행 (N3)**: 무인 자율주행(AC4)엔 "육안" 주체가 없다 → **스크린샷 캡처 + 모델 비전 분석**(빌트인 `verify`/preview)이 1차 eye. visual도 Evidence([2J]) 대상 — *캡처 경로·관찰 내용을 evidence에 인용*("스크린샷 봤다 치고" 통과 금지). **판정 애매·고위험**(색 대비·미세 레이아웃)이면 자율주행 보류하고 사용자에 surface(narrative #4 BROKEN 사다리 준용 — 1줄 알림, 강제 round-trip은 아님).

### 무게 강등 신호 (위 타입에서 도출)

| 신호 | impl-verify 처리 |
|---|---|
| **오라클 있음** (parity/gold/측정/육안) | per-slice 격리 2-stage → **controller 경량 self-review**로 강등 가능. 단 above fresh-reviewer 우선 규칙이 걸린 attempt에는 강등하지 않는다. 진짜 통과 판정은 *오라클 흔적* 인용. |
| **순수이동 (AST 0 diff)** | **fresh agent 금지**. controller self-review + `git diff`/AST 0-diff 확인만. 기계적 이동에 격리 reviewer 한계효용 0 |
| **batch seam** | per-slice 아니라 *독립 실행 가능 seam*에서 1회. 느슨결합·저위험만 묶음 — 독립·고위험 슬라이스는 per-slice 유지 (조기발견 상실 트레이드오프) |

⚠️ 오라클 *낙관 가정 금지* — 애매하면 per-slice 유지 (오판 시 버그가 오라클 단계로 늦게 새어 역추적 비쌈). OPEN이지만 **decision-gated**: 강등은 "안 만들면?"·비용·Evidence를 통과한 판단이어야 한다 ( FORCE/OPEN).

## 절차 (2-stage)

### Reviewer 정신 — *보고서를 믿지 마라*

> **"The implementer finished suspiciously quickly. Their report may be incomplete, inaccurate, or optimistic. You MUST verify everything independently. Verify by reading code, not by trusting report."**
>
> - DO NOT: implementer 보고의 "DONE" 자체를 사실로 받아들임 · 완료 주장 그대로 인용 · 요구사항 해석을 그대로 채택
> - DO: 실제 commit diff·코드 직접 읽기 · 요구사항과 코드 *line by line* 대조 · *빠진 것* + *시키지 않은 추가* 모두 검출

### Stage 1: Spec Compliance Review

1. plan에서 해당 slice 본문 paste (file read X — superpowers "Never make subagent read plan file" 정신)
2. commit diff 점검:
   - `git diff <prev-commit>.HEAD --stat` → touched_files 확인
   - **out_of_slice_touches 검출**: plan slice.touched_files에 없는 파일 발견 시 → BLOCKED ([1C] 신호)
   - **plan 의도 초과 자동 신호** (superpowers `implementer-prompt.md` L51 차용): 생성·확장된 파일이 plan slice 의도 *명백히 초과* (예: slice 1줄 짜리인데 신규 파일 3개 생성, 또는 단일 함수 추가 의도였는데 모듈 신설) → 자동 *important issue* 등록 + status 최소 DONE_WITH_CONCERNS
   - **영향범위(caller) 누락 검출** — `out_of_slice_touches`의 대칭(범위 밖 건드림이 아니라 *범위 안인데 파급 미확인*): touched_files 안에서 *시그니처·동작이 바뀐 public 함수·artifact*마다 `git grep`/AST로 호출처를 열거 → 각 caller가 (a) 같은 슬라이스에서 함께 갱신됐거나 (b) 영향 없음이 직접 확인돼야 한다. 못 닫은 caller/producer/consumer/derived-output은 issue에 기록하되 해소가 아니며 → BLOCKED 또는 NEEDS_CONTEXT다.
3. spec 부합 점검 (코드 *직접 읽기*):
   - **빠진 것**: 요구사항 line-by-line 체크리스트 → 미구현 항목
   - **시키지 않은 추가**: spec 밖 기능·"nice to have" 검출
   - **잘못 해석**: 같은 단어 다른 의미로 구현?
   - attempt 1은 위 검증 유형을 먼저 artifact에 적고, deterministic이면 declared preflight를 **직접 실행**한다. 구현자의 preflight는 coverage 대조용으로만 읽고 reviewer output으로 대체하지 않는다.
   - behavior/integration/judgment이면 declared targeted check와 caller/integration 경로를 직접 실행·대조한다. 이 단계의 slice 검증은 terminal full regression이 아니다.
   - attempt 2 이상은 아래 scoped re-verify 절차가 정한 명령만 직접 실행한다. 이전 attempt의 command/output을 이번 evidence로 복사하지 않는다.
   - 출력 직접 인용 → evidence 필드
4. **Stage 1 통과 조건**: 빠진 것 0 + 시키지 않은 추가 0 + out_of_slice_touches 빈 배열 + 미처리 caller/producer/consumer/derived-output 0

### Stage 2: Code Quality Review

Stage 1 ✅이어야 진입.

1. **[3I] 점검**: 새 클래스·래퍼·매니저 발견 시 "지우면 어떻게 되나?" 자문
2. **[3J] 점검**: 새 공유 모듈 발견 시 "두 번째 사용처 진짜 있나?"
3. **[1D] 점검**: 같은 값·결정이 여러 곳에 있나? (DRY)
4. **gc-skill 임계치**: 현재 세션에 노출된 `gc` skill의 `gc_audit.py`를 실행한다(예: `py -3 <gc_skill_root>/gc_audit.py`). 임계치 초과 있으면 important issue
5. **TDD 흔적 — *red-green 양방향 관찰 강제*** (`verification.type=unit_test`/`tdd-parity`일 때만; artifact/command 슬라이스에 새 TDD를 꾸며내지 않음) ("If you didn't watch the test fail, you don't know if it tests the right thing"):
   - 새 테스트 존재만으로 부족. *실패→통과* 양방향 흔적 필수
   - 구현자가 남긴 실제 RED와 GREEN 명령 출력 모두를 직접 대조한다. commit 분리·`git log`만으로 RED/GREEN을 추정하지 않는다.
   - reviewer는 shared worktree를 revert/restore하지 않는다. 양방향 출력이 없으면 testing 차원 **critical issue**로 BLOCKED하고 `/impl`이 안전한 실행 맥락에서 흔적을 다시 만들게 한다.
6. **Evidence**: 각 검증마다 *실제 실행한* 명령 + 출력 인용. 미실행 명령은 evidence에 기재하지 말 것

### 통합 status

| Stage 1 | Stage 2 | status |
|---|---|---|
| ❌ | — | BLOCKED |
| ✅ | ❌ critical | BLOCKED |
| ✅ | ❌ important만 | DONE_WITH_CONCERNS |
| ✅ | ✅ | DONE |

JSON 저장: `<verify_root>/slice-<N>-attempt-<M>.json` 또는 batch seam artifact.

### Terminal full regression (골 종료 후보마다 1회)

모든 slice gate가 닫힌 뒤, **골 종료를 판정할 바로 그 commit**에서만 plan 또는 프로젝트가 선언한 full-regression command를 한 번 실행한다. per-attempt·per-fix의 편의상 전체 suite를 되풀이하지 않는다. preflight·targeted check가 full regression을 대신한다고 주장하지도 않는다.

- 골 종료를 소유한 impl controller만 `<verify_root>/terminal-<slug>-regression.json`을 쓴다. command, output, terminal-candidate SHA를 남기고, 같은 SHA의 DONE artifact가 있으면 재사용한다. 전체 regression이 선언되지 않았다면 없는 명령을 발명하거나 실행했다고 쓰지 말고 그 사실과 잔여 범위를 명시한다.
- terminal regression이 실패하면 그 후보는 종료하지 않는다. 수정으로 새 후보가 생긴 뒤에만 그 **새 후보**에 대해 1회 다시 실행한다.

> **기준 동기화**: 여기 BLOCK급 기준(out_of_slice 경계 · caller impact-radius · TDD red-green · evidence 무결성)을 추가·변경하면 impl의 dispatch "Your job" 템플릿에도 같은 기준을 적는다. producer(dispatch)-verifier 비대칭 방지. 격리 dispatch subagent는 프롬프트에 없는 기준을 못 지킴.

## 안 하는 것 (Red Flags)

- Stage 2를 Stage 1 통과 전에 시작 (superpowers Red Flags)
- evidence 빈 채 DONE 기재 ([2J])
- **public 시그니처·동작 바꾸고 caller 열거 없이 Stage 1 통과** — impact-radius 미확인 (Stage 1 step 2 caller 누락 검출 생략)
- **미실행 명령을 evidence에 기재** — "Report only what was actually verified" 위반 (OMC `verify` 차용)
- **implementer 보고의 "DONE"을 evidence로 인용** — 그건 보고이지 검증 아님
- 코드 *수정* (검증자 read-only)
- 추상 통과 ("괜찮음", "잘 됐어 보임", "should pass" — superpowers `verification-before-completion` Red Flags)

## 다음 단계 (fix 사이클)

verify status에 따라 자연 흐름 (OMC `ultraqa` 반복 사이클 정신 차용):

| status | 다음 |
|---|---|
| DONE | 다음 slice 또는 골 종료 ADR |
| DONE_WITH_CONCERNS | important issue 본문 paste → `/impl`로 fix 슬라이스 시작 (작은 슬라이스로) → 끝나면 `/impl-verify` 재호출 |
| BLOCKED | critical issue 본문 paste → `/impl` 또는 `/plan` 재검토 → 사이클 반복 *until status=DONE* |
| NEEDS_CONTEXT | 컨트롤러에게 escalate — 사용자 입력 필요 |

**중요**: fix 사이클은 기존 attempt artifact를 덮어쓰지 않는다. 같은 slice의 `attempt M+1`로 기록하며, 새 슬라이스로 위장하지 않는다.

**scoped re-verify (재검증 attempt 2~3)**:
- reviewer는 매 attempt fresh/read-only다. 이전 artifact에서 **issue ID와 요구된 closure**만 받아 scope를 만들고, 이전 reviewer의 결론·명령 출력은 증거로 인용하지 않는다.
- scope는 (a) prior issue가 고쳐진 실제 diff·코드, (b) fix paths, (c) 바뀐 public symbol/artifact의 callers와 producer·consumer·aggregate-output 영향으로 구성한다. 각 항목을 이번 attempt에 직접 읽거나 실행한다. deterministic이면 declared selector로 **영향받은 관계만** 다시 확인하고, behavior/integration/judgment이면 그 caller/integration 경로의 targeted check를 다시 실행한다.
- 다음이면 scoped 가정을 버리고 full slice reverify로 승격한다: preflight/targeted check/fixture·golden·screenshot·measurement의 command·expected 기준·coverage가 바뀜, caller/producer/consumer graph 또는 public behavior가 넓어짐, declared selector로 닫지 못하는 aggregate/shared output까지 파급됨, out-of-slice touch가 생김, 또는 영향 반경을 직접 닫을 수 없음. 마지막 경우 먼저 full reverify를 하고도 반경을 닫지 못하면 `NEEDS_CONTEXT`; 어느 쪽도 DONE이 될 수 없다.
- scoped reverify에서도 Stage 2는 fix-introduced abstraction/DRY/TDD/evidence 문제를 **변경·영향 경로**에 대해 새로 점검한다. 매 attempt에 전체 oracle·전체 regression을 반복하지 않는다.

## Reeval

- DONE인데 실제 결함 발견 사례 2회 → 격리 강화 검토 (옵션 1 promote)
- Stage 2 *놓친 차원* 발견 → 차원 추가
- gc-skill 임계치가 *오탐* 다수 → 임계치 조정

---

## 결정 신호


- '통과' 단언 직전 → [2J] Evidence (verify-report JSON `evidence` 필드 강제)
