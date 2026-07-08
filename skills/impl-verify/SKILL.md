---
name: impl-verify
description: |
  슬라이스 구현 격리 검증 2-stage (spec compliance → code quality) + 오라클 판정 *내장*. superpowers `subagent-driven-development` 패턴 차용.
  **자동 발동 (self-trigger, 라우터 없음)**: 슬라이스 commit 후 "통과" 단언 전 (`slice-N.json` 부재). "impl 검증"·"이 구현 어떻게 보여?"·"impl-verify".
  **Evidence (FORCE)**: 미실행 명령 evidence 금지 · implementer "DONE" 인용 금지 · caller 열거 없이 통과 금지.
  **오라클 (G-B, OPEN)**: 슬라이스마다 오라클 *타입*(tdd-parity/spike/live-dry-run/visual/adversarial)을 판정해 검증법을 *스스로* 고름 — 라우터 수식자 fold. 산출 `.claude/verify-reports/slice-N.json`. 명시: `/impl-verify slice-N`.
---

# /impl-verify — 슬라이스 구현 격리 검증 2-stage (얇은 stub)

> *얇은 stub*. Reeval: sycophancy 2회 등장 시.

> **약어 지도** — 이 문서는 cross-project 수신자가 raw URL로 가져간다. 맥락을 공유하지 않는 cold reader가 외부 문서 없이 읽게:
> - `오라클(oracle)` = 이 슬라이스가 "됐다"를 *무엇으로 판정*하나 — 테스트 통과냐 측정값이냐 육안이냐. 검증법을 정하는 기준
> - `G-B` = 그 오라클 *타입*을 슬라이스마다 판정(아래 표) / `G-C` = visual(UI 육안) 오라클 — 기준은 이 문서
> - `surface` = 게이트가 판단을 강제하지 않고 *트레이드오프만 드러내 보임* / `fold` = 옛 라우터가 쥐던 수식자를 이 게이트 안으로 접어 넣음
> - `seam` = 독립 실행 가능한 이음새 — 저위험 슬라이스를 묶어 1회 검증하는 경계
> - `[2J]` = "통과" 단언 전 실제 명령 출력을 직접 인용(미실행 명령 evidence 금지) / `[1C]` = 슬라이스 밖 파일 건드림 거부 / `[3I]` = 새 클래스·래퍼는 "지우면?" 자문 / `[1D]` = 같은 값·결정이 여러 곳이면 DRY 위반 / `FORCE`·`OPEN` = 슬롯 존재 강제·값은 모델 판단
> - 원칙 전체를 외부 문서로 떠넘기지 말고, 위 약어와 이 스킬 안의 FORCE/OPEN 조건을 우선 적용한다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: 슬라이스 commit 직후 "통과" 단언 전, `.claude/verify-reports/slice-<N>.json` 부재 시
- 자연어: "impl 검증", "이 구현 어떻게 보여?", "impl-verify"
- 명시: `/impl-verify <slice N>`

## 사전 조건

- 해당 슬라이스 commit 존재 (WHY: prefix 있음)
- `Test-Path .claude/plans/<slug>.md` (해당 slice 메타 확인용)
- plan 안 해당 slice의 touched_files 명시되어 있음

## 산출 artifact (강제)

`.claude/verify-reports/slice-<N>.json` — 필수 필드:
- `kind`: "impl-verify"
- `target`: slice N
- `status`: 4상태
- `evidence`: 최소 2개 (각 stage에서 1개씩)
- `issues`: severity 분류
- `touched_files`: 실제 수정 파일 목록
- `out_of_slice_touches`: 빈 배열이어야 [1C] 통과 — 채워져 있으면 BLOCKED
- `self_review`: 4차원

## 오라클 판정 (impl-verify 자체 — 라우터 수식자 fold)

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
| **오라클 있음** (parity/gold/측정/육안) | per-slice 격리 2-stage → **controller 경량 self-review**로 강등. 진짜 통과 판정은 *오라클 흔적* 인용. 아낀 무게는 plan-verify + 오라클 + codex로. 단 plan-verify·codex·오라클은 유지 — 오라클이 못 보는 설계 모순·엣지는 이 셋이 잡음 |
| **순수이동 (AST 0 diff)** | **fresh agent 금지**. controller self-review + `git diff`/AST 0-diff 확인만. 기계적 이동에 격리 reviewer 한계효용 0 |
| **batch seam** | per-slice 아니라 *독립 실행 가능 seam*에서 1회. 느슨결합·저위험만 묶음 — 독립·고위험 슬라이스는 per-slice 유지 (조기발견 상실 트레이드오프) |

⚠️ 오라클 *낙관 가정 금지* — 애매하면 per-slice 유지 (오판 시 버그가 오라클 단계로 늦게 새어 역추적 비쌈). OPEN이지만 **decision-gated**: 강등은 "안 만들면?"·비용·Evidence를 통과한 판단이어야 한다 (`using-methodos` FORCE/OPEN).

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
   - **영향범위(caller) 누락 검출** — `out_of_slice_touches`의 대칭(범위 밖 건드림이 아니라 *범위 안인데 파급 미확인*): touched_files 안에서 *시그니처·동작이 바뀐 public 함수·artifact*마다 `git grep`/AST로 호출처를 열거 → 각 caller가 (a) 같은 슬라이스에서 함께 갱신됐거나 (b) 영향 없음이 직접 확인됐거나 (c) `issues`에 *잔여 불확실성*으로 명시돼야 함. 셋 다 아닌 caller 1개라도 존재 시 → BLOCKED (impact-radius 미확인). "일부만 읽고 파급 못 봄" 방지 — 게이트 통과는 graph/grep·코드·테스트 *합의* 또는 잔여 불확실성 *명시*로만
3. spec 부합 점검 (코드 *직접 읽기*):
   - **빠진 것**: 요구사항 line-by-line 체크리스트 → 미구현 항목
   - **시키지 않은 추가**: spec 밖 기능·"nice to have" 검출
   - **잘못 해석**: 같은 단어 다른 의미로 구현?
   - plan의 verification 명령 *직접 실행* ([2J] Evidence 강제)
   - 출력 직접 인용 → evidence 필드
4. **Stage 1 통과 조건**: 빠진 것 0 + 시키지 않은 추가 0 + out_of_slice_touches 빈 배열 + 미처리 caller 0 ((a)/(b)/(c) 중 하나로 모두 해소)

### Stage 2: Code Quality Review

Stage 1 ✅이어야 진입.

1. **[3I] 점검**: 새 클래스·래퍼·매니저 발견 시 "지우면 어떻게 되나?" 자문
2. **[3J] 점검**: 새 공유 모듈 발견 시 "두 번째 사용처 진짜 있나?"
3. **[1D] 점검**: 같은 값·결정이 여러 곳에 있나? (DRY)
4. **gc-skill 임계치**: `py -3 ~/.claude/skills/gc/gc_audit.py`. 임계치 초과 있으면 important issue
5. **TDD 흔적 — *red-green 양방향 관찰 강제*** ("If you didn't watch the test fail, you don't know if it tests the right thing"):
   - 새 테스트 존재만으로 부족. *실패→통과* 양방향 흔적 필수
   - 검증 방법: `git log --oneline <prev>.HEAD -- <test_path>` 에 red commit + green commit 분리, **또는** verify 단계에서 *fix를 임시 revert → 테스트 실행해서 실제 fail → restore → 다시 pass* 사이클 직접 실행
   - 양방향 관찰 흔적 없으면 → testing 차원 *important issue* + evidence에 사이클 명령 출력 인용
6. **Evidence**: 각 검증마다 *실제 실행한* 명령 + 출력 인용. 미실행 명령은 evidence에 기재하지 말 것

### 통합 status

| Stage 1 | Stage 2 | status |
|---|---|---|
| ❌ | — | BLOCKED |
| ✅ | ❌ critical | BLOCKED |
| ✅ | ❌ important만 | DONE_WITH_CONCERNS |
| ✅ | ✅ | DONE |

JSON 저장: `.claude/verify-reports/slice-<N>.json`.

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
| DONE | 다음 slice 또는 골 종료 결정 기록 |
| DONE_WITH_CONCERNS | important issue 본문 paste → `/impl`로 fix 슬라이스 시작 (작은 슬라이스로) → 끝나면 `/impl-verify` 재호출 |
| BLOCKED | critical issue 본문 paste → `/impl` 또는 `/plan` 재검토 → 사이클 반복 *until status=DONE* |
| NEEDS_CONTEXT | 컨트롤러에게 escalate — 사용자 입력 필요 |

**중요**: fix 사이클은 *기존 slice-N.json을 덮어쓰지 않음*. 새 슬라이스로 처리 (각 사이클이 *재현 가능 흔적* — [2J] 그대로).

**scoped re-verify (재검증 attempt 2~3)**:
- attempt 1만 코드베이스 fresh 독립 재독(Stage 1+2 풀). **fix 재검증 attempt는 전체 재독 금지** — 이전 `slice-<N>-attempt-<M>.json`의 `issues`(걸린 것) + `git diff <prev-fix-sha>.HEAD`만 읽고 범위 한정:
  - 걸린 issue가 fix됐나 (해소 판정은 diff 직접 확인 — JSON 주장 인용 금지)
  - touched_files에 fix-introduced regression 생겼나
- **scope 이탈 안전판**: fix diff가 `out_of_slice_touches` 신호(슬라이스 밖 광범위 수정) 내면 scoped 가정 깨짐 → 그 라운드만 **full 재독으로 승격**.
- 모델: scoped라 이미 쌈 → opus 유지. 더 짜려면 재검증 attempt만 sonnet 강등 *가능*(옵션, 강제 아님).

## Reeval

- DONE인데 실제 결함 발견 사례 2회 → 격리 강화 검토 (옵션 1 promote)
- Stage 2 *놓친 차원* 발견 → 차원 추가
- gc-skill 임계치가 *오탐* 다수 → 임계치 조정

---

## 실행 전후 확인

- '통과' 단언 직전 → [2J] Evidence (verify-report JSON `evidence` 필드 강제)
