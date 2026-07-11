---
name: impl-verify
description: |
  Fresh-context, read-only verification of one implemented slice: spec coverage,
  caller/producer/consumer impact, and code quality when source code changed.
  **Self-trigger** after a slice commit and before saying it is complete when no
  `slice-<N>-attempt-<M>.json` covers the candidate. Classify the slice once as
  `deterministic_artifact_or_command` or `behavior_integration_or_judgment`.
  **Evidence** is actual command output only; an unverified caller or unavailable
  reviewer cannot produce DONE. User-facing NEEDS_CONTEXT text stays plain Korean.
---

# /impl-verify — 슬라이스 검증 gate

이 스킬이 구현 검증의 실행 지점이다. 검증자는 매 attempt마다 새 컨텍스트의
`impl-verify-reviewer`로 실행하고 read-only로 남는다. 구현자의 DONE 보고나
이전 attempt의 출력은 증거가 아니다.

## 트리거와 사전 조건

- 슬라이스 commit 뒤, 완료 단언 전에 현재 후보를 덮는
  `<verify_root>/slice-<N>-attempt-<M>.json`이 없을 때 자동 발동한다.
- 명시 호출: `/impl-verify <slice N>` 또는 "impl 검증", "이 구현 어떻게 보여?".
- nearest `AGENTS.md`와 plan frontmatter에서 `plan_root`/`verify_root`를 먼저
  정한다. plan의 해당 slice 본문과 `touched_files`를 reviewer prompt 안에
  붙여 넣는다.

## 산출 artifact

`<verify_root>/slice-<N>-attempt-<M>.json`은 다음을 포함한다.

- `kind`, `target`, `attempt`, `status`(DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT)
- `verification_class`: `deterministic_artifact_or_command` 또는
  `behavior_integration_or_judgment` (slice에서 한 번 결정)
- `stage_results.spec`, `stage_results.quality`(PASS/FAIL/NEEDS_CONTEXT/SKIPPED)
- `evidence`: 이번 reviewer가 실제 실행한 명령과 출력. Stage 1은 최소 1개,
  Stage 2를 실행했으면 Stage 2도 최소 1개
- `stage2_skip_reason`: quality가 SKIPPED일 때 필수
- `issues`: severity와 stable issue ID, `touched_files`, `out_of_slice_touches`
- `reviewer_mode=fresh_subagent`, `reviewer_role=impl-verify-reviewer`,
  `self_review` 4차원

reviewer를 dispatch할 수 없거나 evidence가 비면 DONE/DONE_WITH_CONCERNS를
쓰지 말고 `NEEDS_CONTEXT`로 닫는다. caller, producer, consumer, derived output
중 하나라도 어디까지 영향을 받는지 직접 닫히지 않으면 BLOCKED 또는
NEEDS_CONTEXT다.

## 검증 분류와 attempt 1

이 분류만 사용한다. plan의 `verification.type`과 `unit_test`/`tdd-parity`는
실행법을 고르는 메타데이터일 뿐 두 번째 분류 체계를 만들지 않는다.

| 분류 | 판정 | fresh reviewer의 attempt 1 |
|---|---|---|
| `deterministic_artifact_or_command` | 같은 입력에서 artifact, fixture, hash, schema 또는 닫힌 command의 기계적 참/거짓이 나옴 | **spec coverage + oracle adequacy + integrated preflight 독립 재실행만** 한다. preflight는 선언된 producer→consumer→derived-output edge와 좁은 selector를 실제로 따라가야 한다. source code/abstraction이 없으면 Stage 2, gc, TDD를 `SKIPPED`하고 이유를 기록한다. source code/abstraction이 있으면 그 변경 경로에 한해 Stage 2를 추가한다. |
| `behavior_integration_or_judgment` | public 동작, caller 조합, integration, 외부 시스템 또는 판단이 실행 성공만으로 닫히지 않음 | full 2-stage를 실행한다. Stage 1에서 spec과 영향 graph를 닫고, 통과한 뒤 Stage 2에서 quality·gc·적용 가능한 TDD를 확인한다. |

구현자는 deterministic 경로에서 commit 전에 preflight의 command, pass 기준,
producer→consumer→derived-output coverage, scope selector를 선언하고 실행한다.
그 결과(command/output/exit/coverage)는 조기 결함 탐지용 handoff일 뿐이다.
reviewer는 같은 preflight를 독립 재실행하고 자신의 출력만 evidence로 쓴다.
실패·미선언·coverage 누락은 BLOCKED다.

`verification.type=unit_test` 또는 `tdd-parity`이면 새 테스트의 실제 RED와
GREEN 출력 모두 필요하다. commit log로 RED를 추정하지 않는다. reviewer는
shared worktree를 revert/restore하지 않으며, 양방향 출력이 없으면 critical
issue로 BLOCKED한다.

## Stage 1 — spec과 영향

공통 spec coverage는 inline slice spec과 실제 diff, `touched_files`,
`out_of_slice_touches`를 대조한다. 범위 밖 파일·plan 의도 초과·요구사항의
누락·무단 추가·오해는 BLOCKED다.

- deterministic attempt 1은 여기서 **spec coverage + oracle adequacy +
  integrated preflight 재실행**만 한다. caller, producer, consumer, derived
  output 확인은 integrated preflight가 선언된 edge를 따라가는 일부이며 별도
  broad review로 다시 실행하지 않는다.
- behavior/integration/judgment는 바뀐 public symbol/artifact의 caller,
  producer, consumer, derived output을 `git grep`/AST와 targeted command로
  열거하고 영향 없음도 직접 확인한다.
- 모든 경우 실제 reviewer output만 `evidence`에 직접 인용한다. 이전 attempt의
  명령이나 구현자 보고를 복사하지 않는다.

Stage 1이 PASS일 때만 Stage 2로 간다.

## Stage 2 — 필요한 경우의 quality

behavior/integration/judgment attempt 1은 full Stage 2를 실행한다. deterministic
경로는 source code/abstraction이 실제로 바뀐 경우에만 변경·영향 경로에 한해
실행한다. 새 abstraction([3I]/[3J]), 중복 결정([1D]), gc 임계치와 적용 가능한
TDD red-green/evidence를 점검한다. source code가 바뀌지 않은 deterministic
경로에서는 Stage 2/gc/TDD를 실행하지 않고 `stage2_skip_reason`에
`data-only: source code unchanged` 같은 구체적 이유를 남긴다.
behavior/integration/judgment attempt 1에서 quality를 SKIPPED로 쓰는 것은 무효다.

| Stage 1 | Stage 2 | status |
|---|---|---|
| FAIL | — | BLOCKED |
| PASS | critical FAIL | BLOCKED |
| PASS | important만 | DONE_WITH_CONCERNS |
| PASS | PASS 또는 SKIPPED(정당한 이유) | DONE |

## BLOCKED fix 후 재검증

기존 artifact를 덮어쓰지 않고 같은 slice의 `attempt M+1`을 만든다. reviewer는
매번 fresh/read-only다. 이전 artifact에서 prompt로 넘길 수 있는 것은 stable
issue ID와 요구된 closure뿐이며, 이전 결론·명령·출력은 이번 evidence가 아니다.

기본은 scoped reverify다. 범위는 다음 세 가지로만 닫는다.

1. prior issue가 실제로 닫혔는지
2. fix의 changed paths
3. 바뀐 symbol/artifact의 caller 및 producer→consumer→derived-output 영향

deterministic narrow fix이고 oracle/acceptance criteria와 public/caller graph가
그대로이며 위 영향이 모두 닫히면, deterministic은 영향받은 selector/preflight만,
behavior/integration narrow fix도 영향받은 caller/integration targeted check만
다시 실행한다. source
code/abstraction 변경이 있으면 그 경로의 Stage 2만 scoped로 실행하고, 없으면
Stage 2/gc/TDD를 건너뛴 이유를 기록한다.

다음 중 하나면 full slice reverify로 승격한다: oracle 또는 acceptance criteria
변경, public API/public-caller graph 변경, out-of-slice touch, aggregate/shared output까지
selector로 닫히지 않음, 또는 영향 범위가 아직 미폐쇄. full reverify에서도 fresh
reviewer와 실제 evidence를 사용한다. scope가 끝내 닫히지 않으면 DONE할 수 없다.

## 최종 후보의 full regression

모든 slice gate가 닫힌 뒤 goal owner가 골 종료를 판정할 **최종 candidate SHA에서
한 번만** 선언된 full-regression command를 실행한다. 별도 terminal artifact를
만들지 않고 최종 slice attempt artifact의 `terminal_regression`에 candidate SHA,
owner, command, exit code, 실제 output을 기록한다. 선언된 command가 없으면
`NOT_DECLARED`와 남은 범위를 기록하고 없는 명령을 발명하지 않는다. 실패한
후보는 종료하지 않으며, fix로 새 최종 후보가 생긴 경우에만 그 SHA에서 다시
한 번 실행한다.

## 금지

- Stage 1 전에 Stage 2 시작
- 실행하지 않은 명령·출력 또는 구현자 DONE을 evidence로 사용
- caller/producer/consumer/derived-output 영향 미확인 상태의 DONE
- reviewer가 코드나 shared worktree를 수정

---

## 결정 신호

- 슬라이스 완료 단언 직전: 실제 evidence와 impact graph를 확인한다.
- 최종 goal 종료 직전: final slice artifact의 `terminal_regression`을 확인한다.
