---
name: impl
description: |
  승인된 plan의 슬라이스를 *한 슬라이스씩* 구현 (model-driven 자율주행). 산출은 git commit (WHY: prefix).
  **자동 발동 (self-trigger, 라우터 없음)**: plan approved + plan-verify DONE + 해당 slice 미구현(commit·verify-report 부재)일 때. "구현"·"implement"·"이 슬라이스 만들어"·"이어가"·"끝까지 진행"에서 직접 진입한다.
  **하네스 경로 (FORCE)**: nearest `AGENTS.md`/plan 관례로 `plan_root`·`verify_root`를 정한다. 프로젝트가 `.claude/plans`를 쓰면 `.Codex/*` 기본값을 쓰지 않는다.
  **impl 구간 자율주행 (FORCE)**: 사용자 결정 공간이 해소된 뒤에는 모든 slice commit, configured impl-verify gates, 다파일∨다flow `impl-novelist`까지 이어간다.
  **멈춤 조건 (FORCE)**: out-of-slice, plan 의도 초과, NEEDS_CONTEXT, 사용자 경험 what 변경·비가역·사용자 자산 영향이 새로 생기면 멈춰서 쉬운 말로 보고/질문한다.
  **실행모드 (G-A, OPEN)**: inline vs fresh-subagent dispatch는 context-locality + coupling 기준으로 모델이 판단한다. 명시 호출은 선택사항: `/impl slice id`.
---

# /impl — 슬라이스 구현 스킬 (얇은 stub)

> *얇은 stub*: 핵심 절차 + 산출 형식만 포함. 실사용 데이터로 본문 확장 예정.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: plan status=approved + plan-verify status=DONE + 해당 slice의 commit/verify-report 부재 시
- 자연어: "구현", "implement", "이 슬라이스 만들어"
- 명시: `/impl <slice id 또는 slug>`

## 사전 조건 (강제)

- **하네스 경로 결정**: nearest `AGENTS.md`와 plan frontmatter를 먼저 읽어 `plan_root`와 `verify_root`를 정한다. 예: 프로젝트가 `.claude/plans/`를 정본으로 선언하면 `plan_root=.claude/plans`, `verify_root=.claude/verify-reports`; 별도 선언이 없을 때만 Codex 기본값(`.Codex/plans`, `.Codex/verify-reports`)을 쓴다.
- `Test-Path <plan_root>/<slug>.md` ✅
- plan frontmatter status=approved
- `Test-Path <verify_root>/plan-<slug>-verify-attempt-*.json` (최신) + status=DONE/DONE_WITH_CONCERNS (D13 attempt schema)
- 현재 slice id의 `touched_files` 명시되어 있음
- plan frontmatter `drive_config.dispatch`가 있거나 프로젝트가 요구하면 현재 slice의 `mode`(inline/sdd)와 `model`을 읽는다. 요구되는데 없으면 구현하지 말고 plan으로 돌아가 `drive_config`를 합성한다.

위 부족하면 `/plan` 또는 `/plan-verify`로 돌아감.

## impl-verify gate controller (D24 ralph, 후속)

각 슬라이스 commit 후 *자동*으로 `impl-verify` gate를 만족시킨다. 별도 gate 참고문서를 만들지 않는다.
`impl-verify` skill이 fresh reviewer를 쓸지, oracle/self-review/AST0/batch seam으로 강등할지 결정한다.
여기서 "각 슬라이스"는 **gate 만족 지점**이지 full per-slice reviewer 고정이 아니다. `impl-verify`가 batch seam을 택하면 여러 저위험 슬라이스를 한 seam artifact로 만족시킬 수 있다.

- attempt 1 실행 → JSON 산출 (`slice-<N>-attempt-1.json`)
- status=BLOCKED → impl이 fix → attempt 2 →.. attempt 10
- attempt 10 BLOCKED 또는 `repeated_from_attempt`로 동일 critical 재등장 → `escalation_required: true` + 사용자 escalate
- **자율주행 자리** — 사용자 의도 "끝까지 자동" 정합. model-driven 순차 구동에서 머무름 (D28 cache 윈도우)
- **무한 spinning 가드**: ralph 루프 자체의 내부 카운터(N=10)가 가드 — 빌트인 turn 한도에 의존 안 함 (P0-2  Reeval 참고)

attempt M 실행 시 attempt M-1 결과 paste 전달 → `impl-verify` gate가 `repeated_from_attempt` 판정.

## Cross-runtime adversarial review

Codex sessions do not call Codex as an external reviewer. If a project declares a
separate reviewer runtime, run that review after all configured `impl-verify`
gates and any required `impl-novelist` pass. Record the result as an advisory
artifact under `<verify_root>`; do not let the advisory replace Methodos
`impl-verify` evidence.

## 산출 artifact (강제)

각 슬라이스 끝에:
- **git commit** with WHY body:
  ```
  <한 줄 제목>

  WHY: <한 줄 결정> | 비용(지금/부채): Xm/Ym | Reeval: <조건>
  Slice: <slice id>
  Touched: <touched_files 목록>
  ```
- (선택) `<verify_root>/slice-<N>.json` 또는 batch seam artifact — 이건 `/impl-verify`가 산출

## 절차 (얇음)

1. **사전 조건 점검**: 위 4개 모두 통과. 안 되면 escalate.
2. **plan slice 본문 paste**: plan frontmatter에서 해당 slice 추출. *본문 안에 inline*. 파일 읽기 의존 X (superpowers "Never make subagent read plan file" 정신).
3. **구현**:
   - touched_files 안에서만 작업
   - *슬라이스 외 파일 건드릴 신호* 시 즉시 멈춤·보고 ([1C] 누더기 위 누더기 거부)
   - **plan 의도 초과 자동 신호** (superpowers `implementer-prompt.md` L51 차용): 만드는 파일이 plan slice 의도를 *명백히 넘어 자라면* (예: 단일 함수 → 모듈 신설) → 분리 시도 X, 즉시 멈추고 *DONE_WITH_CONCERNS*로 보고. plan 가이드 없이 자체 분할 금지.
   - [3J] 추출 시점: *재사용* 목적 공유 모듈은 같은-이유 2차 사용처 전 분리 X (단 크기·응집 분해·사용자 명시 요청은 예외 — 호출처 1개여도 OK)
   - **영향범위(caller) 확인**: 슬라이스가 *public 시그니처·동작*을 바꾸면 `git grep`/AST로 호출처를 열거 → 같은 슬라이스에서 함께 갱신하거나 / 영향 없음을 직접 확인하거나 / 범위상 못 건드리면 *잔여 불확실성*으로 보고. **touched_files 안만 보는 게 함정 — 파급은 밖에 있을 수 있음.** (impl-verify가 미처리 caller 1개라도 있으면 BLOCK — impact-radius 미확인.)
   - **TDD red-green (테스트 오라클 슬라이스 — verification.type=unit_test/tdd-parity)**: plan Steps의 5-step 따름 — 실패 테스트 먼저 → 실행해 *RED 관찰* → 최소 구현 → 실행해 *GREEN 관찰* → commit. red→green 양방향 흔적 필수(impl-verify 강제 검증). inline·dispatch 양쪽 동일 — dispatch 시엔 아래 위임 템플릿이 이를 subagent에 *명시 전달*(격리라 프롬프트에 없으면 모름).
4. **실행모드 선택 (G-A — inline vs fresh-subagent dispatch, OPEN)**:

   oracle 수식자의 *쌍대* 결정. 라우터가 정해주지 않는다 — 게이트가 아래 trade-off를 *surface*하고 모델이 판단한다 (rigid rule 아님, OPEN = decision-gated judgment):
   - **기준 = context-locality**(컨트롤러가 이미 이 코드를 쥐고 있나) + **coupling**(슬라이스가 다른 슬라이스와 파일 공유·의존하나)
   - 둘 다 yes(**보유 + 결합**) → **inline** (dispatch 격리이득 < 재로딩 비용) ← *중간 케이스, 이전 harness에 누락됐던 자리* (실전 실사용 gap)
   - **isolable + 미보유**(독립·큰 슬라이스, est_min ≥ 15 또는 touched ≥ 5) → **dispatch** (아래 템플릿)
   - **순수이동(AST 0 diff)** → inline (controller self-review + AST diff만, 격리 한계효용 0)
   - 작은·로컬 슬라이스 → 컨트롤러 직접 (inline)

   > **불변식 (dispatch = isolated subagent의 유일한 채널)**: subagent는 세션 상속이 없어 *프롬프트에 적힌 것만* 안다. 따라서 impl-verify가 **BLOCK으로 강제하는 기준(out_of_slice 경계 · caller impact-radius · TDD red-green · evidence 무결성)을 모두 여기서 echo**한다. impl-verify에 새 BLOCK 기준이 생기면 이 템플릿도 동기 (같은 BLOCK 기준을 양쪽에 맞춘다).

   위임(dispatch) 시 prompt 형식 (Task tool, general-purpose):
   ```
   You are implementing Task <slice id> from plan <slug>.

   ## Context (DO NOT inherit my session — read only what's below)
   - Plan slice 본문 (paste 전체, file read 금지):
     <plan frontmatter에서 해당 slice 전체 inline paste>
   - touched_files: <목록>
   - verification 명령: <plan에 기재된 명령>
   - WHY body 필수 형식: <impl 산출 artifact 참고>

   ## Your job
   - touched_files 안에서만 작업
   - 슬라이스 외 파일 신호 시 즉시 멈춤·보고
   - plan 의도 초과 자라면 멈추고 DONE_WITH_CONCERNS
   - **영향범위(caller) 확인**: public 시그니처·동작을 바꾸면 `git grep`으로 호출처 열거 → 같은 슬라이스에서 갱신 / 영향 없음 직접 확인 / 범위상 못 건드리면 *잔여 불확실성*으로 보고. **touched_files 밖이라고 무시 금지** — impl-verify가 미처리 caller 1개라도 있으면 BLOCK(impact-radius).
   - **TDD red-green 강제 (테스트 오라클 슬라이스 — verification.type=unit_test 또는 tdd-parity)**: 테스트 먼저 작성 → 실행해서 *실패(RED) 관찰* → 최소 구현 → 실행해서 *통과(GREEN) 관찰* → commit. **red→green 양방향 흔적을 반드시 남길 것** (red commit·green commit 분리, 또는 fail→pass 사이클 출력 인용) — impl-verify가 이 흔적을 *강제 검증*하므로 없으면 BLOCK 후 재작업. "구현+통과 테스트 한 번에" 금지(실패를 안 보면 테스트가 맞는 걸 검증하는지 모름 — superpowers TDD). *artifact/spike/visual 등 테스트 없는 슬라이스*는 plan의 verification 명령 실행·출력으로 대체.
   - 끝나면 WHY: prefix commit + self-review 4차원(completeness·quality·discipline·testing) 보고

   ## Report 4 상태
   DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
   ```

   **주의** (superpowers Red Flags):
   - "Never make subagent read plan file" — plan 본문은 *paste*, file path 던지지 말 것
   - subagent에 컨트롤러 세션 컨텍스트 *상속 금지* — 위 paste만으로 self-contained
   - 모델 선택: 1-2 파일 mechanical → cheap, multi-file integration → standard, architecture/design → most capable
5. **commit + WHY**:
   - WHY body 강제 (조건문이 매 턴 측정)
6. **다음 슬라이스 또는 `/impl-verify` 호출**

## 안 하는 것

- 슬라이스 외 파일 *수정* (읽기는 OK)
- WHY body 누락 commit
- 한 commit에 여러 슬라이스 묶음
- *증상 봉합* 결정 ([1A] 원인 2번 자문)
- 가짜 추상화 ([3J] 한 사용처뿐인 재사용 목적 분리는 보류)

## 다음 단계

- 슬라이스 끝 → `/impl-verify` 격리 검증 (2-stage)
- 검증 DONE → 다음 슬라이스
- 검증 DONE_WITH_CONCERNS / BLOCKED → fix 슬라이스로 사이클 (`/impl-verify`의 "다음 단계" 표 참고)
- 모든 슬라이스 DONE + configured impl-verify gates DONE → (다파일 ∨ 다flow) `impl-novelist` narrative #4 → (별도 reviewer runtime이 설정된 대형·아키텍처 변경 시) runtime advisory review 1회 → **(선택, G-D) 전체 diff `/simplify` 1회 마무리 패스 — 값 있을 때만 (OPEN)** → 결정 기록 또는 `WHY:` 요약 + 골 종료

## Reeval

- 큰 슬라이스 위임 패턴이 *진짜 반복*인지 (≥3회) → 위임 형식 본문 확장
- 슬라이스 외 파일 신호 *오탐* 사례 → 정의 명확화

---

## 결정 신호


- 슬라이스 commit 직전 → [3H] 한 슬라이스 단독 동작·검증 가능 / [1C] 누더기 거부
- (다파일 ∨ 다flow) `impl-novelist` narrative #4 DONE 후, 별도 reviewer runtime이 설정된 대형·아키텍처 변경 → runtime advisory review 1회, 최종 diff 대상·advisory-fold ([2J] cross-runtime Evidence)
