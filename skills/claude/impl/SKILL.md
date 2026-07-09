---
name: impl
description: |
  Implement an approved plan's slices *one slice at a time* (model-driven autonomous drive). Output is a git commit (WHY: prefix).
  **Self-trigger (no router)**: when plan approved + plan-verify DONE + that slice is unimplemented (no commit/verify-report). "구현", "implement", "이 슬라이스 만들어".
  **Execution mode (G-A, OPEN)**: only *surface* whether to write the slice inline vs dispatch to a fresh subagent, judged by context-locality (does the controller already hold the code) + coupling (shared/dependent files) — the *call* is the model's.
  **[1C] reject patchwork (FORCE)**: stop and report on signals of out-of-slice files or exceeding plan intent. Explicit: `/impl slice-id`.
---

# /impl — 슬라이스 구현 스킬 (얇은 stub)

> *얇은 stub*: 핵심 절차 + 산출 형식만 포함. 실사용 데이터로 본문 확장 예정.

> **약어 지도** — 이 문서는 cross-project 수신자가 raw URL로 가져간다. 맥락을 공유하지 않는 cold reader가 외부 문서 없이 읽게:
> - `G-A` = 실행모드 결정 — `inline`(컨트롤러가 직접 짬) vs `sdd`/dispatch(격리 서브에이전트로 떼어 보냄). 기준은 이 문서 §4
> - `surface` = 게이트가 판단을 강제하지 않고 *트레이드오프만 드러내 보임* — 값은 모델이 판단
> - `ralph` = impl-verify 자동 재시도 루프(내부 카운터 N=10) / `advisory-fold` = 차단 없이 기록만(todos·사용자 알림)
> - `narrative #4` = 출하 직전 실사용 서사 게이트(impl-novelist) / `G-D` = 마지막 `/simplify` 1회 패스
> - `[1C]` = 임시방편 위에 또 임시방편 안 쌓음(둘 다 갈아엎는 게 먼저) / `[3J]` = 재사용 추출은 두 사용처가 같은 이유로 변할 때만 / `[1A]` = 증상 말고 원인까지 2번 자문 / `FORCE`·`OPEN` = 슬롯 존재는 강제·그 값은 모델 판단
> - 원칙 전체를 외부 문서로 떠넘기지 말고, 위 약어와 이 스킬 안의 FORCE/OPEN 조건을 우선 적용한다.

## 트리거 (self-trigger — 라우터 없음)

- 자동 발동: plan status=approved + plan-verify status=DONE + 해당 slice의 commit/verify-report 부재 시
- 자연어: "구현", "implement", "이 슬라이스 만들어"
- 명시: `/impl <slice id 또는 slug>`

## 사전 조건 (강제)

- `Test-Path .claude/plans/<slug>.md` ✅
- plan frontmatter status=approved
- `Test-Path .claude/verify-reports/plan-<slug>-verify-attempt-*.json` (최신) + status=DONE/DONE_WITH_CONCERNS (D13 attempt schema)
- 현재 slice id의 `touched_files` 명시되어 있음
- plan frontmatter `drive_config.dispatch`에 현재 slice의 `mode`(inline/sdd) 기재 — **부재 시 멈춤·보고** (자율주행 진입 정책 누락, plan으로 돌아가 drive_config 합성). 2차 그물 — plan 승인 ask를 우회해 impl 직행한 경우 대비 (이 슬롯은 plan의 drive_config에서 닫힘).

위 부족하면 `/plan` 또는 `/plan-verify`로 돌아감.

## impl-verify 호출 controller (D24 ralph)

각 슬라이스 commit 후 *자동* impl-verify-reviewer 호출:

- attempt 1 호출 → JSON 산출 (`slice-<N>-attempt-1.json`)
- status=BLOCKED → impl이 fix → attempt 2 → .. attempt 10
- attempt 10 BLOCKED 또는 `repeated_from_attempt`로 동일 critical 재등장 → `escalation_required: true` + 사용자 escalate
- **자율주행 자리** — 사용자 의도 "끝까지 자동" 정합. model-driven 순차 구동에서 머무름 (D28 cache 윈도우)
- **무한 spinning 가드**: ralph 루프 자체의 내부 카운터(N=10)가 가드 — 빌트인 turn 한도에 의존 안 함

attempt M 호출 시 attempt M-1 결과 paste 전달 → impl-verify-reviewer가 `repeated_from_attempt` 판정.

## Codex cross-model 적대 게이트 (대형·아키텍처 변경, 1회 loop X)

**왜**: impl-verify-reviewer 포함 모든 검증자가 Claude 한 가족(fable/opus) → 공유 맹점. codex(GPT-5.4)로 cross-model 1회 적대 검증.

**자리**: *진짜 맨 끝* 게이트 — 모든 슬라이스 impl-verify 통과 **+ (다flow) narrative #4 status DONE 후**, 골 종료 직전 1회. codex만 loop가 없으니 *코드가 바뀌는 마지막 게이트(narrative #4 fix 루프) 뒤*에 와야 최종 출하 diff를 본다. per-slice 아님 (whole-branch 1회 — per-slice×N = 사실상 loop).

**활성화 (self-scope — 라우터 없음)**: 게이트가 변경 규모를 *자체 평가*해 **대형·아키텍처·보안 변경**(창발 L, 또는 결정 자리 많은 M+D33 — decision-reviewer D25/D33 조건 재사용)이면 자동 활성. 그 외(작은 M·S·XS)는 skip — codex 호출·artifact 생성 안 함. (tier는 사용자 선언 라벨이 아니라 자체 평가 근거 — `using-methodos`.)

**절차** (컨트롤러 1턴, foreground — background polling은 model-driven 순차 구동에 결과 회수 행위자가 없어 못 씀):
0. **precheck**: codex CLI 가용? 아니면 dispatch 생략 + 1회 안내 "대형·아키텍처 변경엔 codex 게이트 있음 — codex 설치/로그인 시 cross-model 검증 활성. 지금은 skip." → artifact `verdict: "error"`, `status: "SKIPPED"` 기록 후 통과.
1. **base 결정 + 빈-diff precheck**: plan frontmatter `approved_plan_revision` SHA. 이 시점엔 모든 슬라이스가 *커밋됨* → working-tree diff가 비어 있으니 **반드시 branch-diff 모드** (`--base <approved_plan_revision>`). **codex 부르기 전 `git diff --shortstat <base>.HEAD`로 diff 비었는지 확인 — 비어 있으면 codex 호출 생략하고 `status: "SKIPPED"`(verdict `error`, reason "empty_diff: base 오설정 의심") 기록.** (smoke test 실측: codex는 빈 diff에 **거짓 `approve` 반환** → 그대로 믿으면 거짓 DONE. 빈 diff = base 설정 문제이지 "결함 없음"이 아님.)
2. **foreground + timeout 단일 호출** (argv는 *분리 토큰* — 따옴표 한 덩어리면 `--base` 인식 못 해 "nothing to review"로 빠짐, smoke test 검증): `node <plugin-root>/scripts/codex-companion.mjs adversarial-review --wait --base <approved_plan_revision>`를 *bounded timeout*(예: 5분)으로 1회 실행. `<plugin-root>`는 절대 경로(예 `<runtime-plugin-cache>/openai-codex/codex/<ver>`) — plugin-root env가 없을 수 있으므로 절대 경로 권장. dispatch+capture+timeout이 한 Bash 호출에 (cross-turn polling 없음). 1회·맨끝이라 이 턴 1개 block 허용.
3. **결과 → artifact** (`.claude/verify-reports/codex-impl-<slug>.json`). 저장 필드: `kind: "codex-impl"`, `target_slug`, `base`, `status`, `verdict`, `raw_review`, `findings`, `created_at`. stdout은 *렌더 markdown*(raw JSON 아님, smoke test 실측):
   - stdout에서 `Verdict: approve` grep → `status: "DONE"`
   - `Verdict: needs-attention` grep → `status: "DONE_WITH_CONCERNS"` + advisory-fold(4단계). `raw_review`에 stdout 원문 저장, findings는 `- [high|medium|low]` 줄에서 best-effort 추출.
   - **빈 stdout·verdict 줄 부재·error·timeout 초과** (사용자 실측: codex 가끔 무응답, 신뢰 과다 금지) → `verdict: "skipped_no_response"`/`"error"`, `status: "SKIPPED"` + 한 줄 알림 "Codex 무응답/미완료 — 게이트 skip하고 진행 (Claude 검증은 이미 통과)". **재시도 없음.**
4. **advisory-fold** (loop 없어 auto-fix-retry X — model-driven 자율주행 공간이라 루프 중 사용자 interaction 아님, *기록*만):
   - findings 중 `severity ∈ {critical, high}` → artifact `fold.surfaced_to_user`에 한 줄씩 (사용자는 *골 종료 후* 읽음). confidence는 보조(동률 시 우선).
   - 나머지(medium/low) → `fold.todos_appended` + `.claude/todos.md` append.
   - **하드 차단(BLOCKED) 없음** — 새 사용자 게이트 안 만듦.

**핵심 불변식**: codex는 *advisory*다. Claude 검증(impl-verify)·narrative #4를 *대체하지 않고 보완*한다. codex 무응답·error·미설치여도 골은 진행 — 게이트는 "codex 1회 호출 시도하고 결과를 기록했다"로 충족(SKIPPED 포함 통과). codex *추론*만 외부(Claude 토큰 X); 게이트 오케스트레이션은 Claude 턴 1개 소비.

## 산출 artifact (강제)

각 슬라이스 끝에:
- **git commit** with WHY body:
  ```
  <한 줄 제목>

  WHY: <한 줄 결정> | 비용(지금/부채): Xm/Ym | Reeval: <조건>
  Slice: <slice id>
  Touched: <touched_files 목록>
  ```
- (선택) `.claude/verify-reports/slice-<N>.json` — 이건 `/impl-verify`가 산출

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

   **plan `drive_config.dispatch`가 이 슬라이스의 provisional mode(inline/sdd)·dispatched `model`을 이미 정함** (plan § drive_config). 그걸 *기본*으로 받되, 컨텍스트가 달라졌으면 이탈 가능(OPEN) — 단 이탈이 파급 범위(blast-radius)를 키우면(되돌리기 비싼 판단 슬라이스를 sdd 격리에서 inline으로 끌어내림 등) 경고. dispatch 시 subagent `model`은 drive_config 값 따름 (effort는 per-slice 레버 없음 — controller 단일값 상속).

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
- 모든 슬라이스 DONE → (다flow) narrative #4 → (narrative #4 DONE 후, 대형·아키텍처 변경 시) Codex 적대 게이트 1회 → **(선택, G-D) 전체 diff `/simplify` 1회 마무리 패스 — 값 있을 때만 (OPEN)** → 결정 기록 또는 `WHY:` 요약 + 골 종료

## Reeval

- 큰 슬라이스 위임 패턴이 *진짜 반복*인지 (≥3회) → 위임 형식 본문 확장
- 슬라이스 외 파일 신호 *오탐* 사례 → 정의 명확화

---

## 실행 전후 확인

- 슬라이스 commit 직전 → [3H] 한 슬라이스 단독 동작·검증 가능 / [1C] 누더기 거부
- (다flow) narrative #4 DONE 후 (대형·아키텍처 변경) → Codex cross-model 적대 게이트 1회, 최종 diff 대상·advisory-fold ([2J] cross-model Evidence)
